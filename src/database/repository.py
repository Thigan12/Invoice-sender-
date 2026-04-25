import datetime
from .connection import get_connection

class DataRepository:
    @staticmethod
    def get_all_customers_summary(search_query=None):
        """Returns customers with info from their ABSOLUTE LATEST invoice, including address."""
        conn = get_connection()
        cursor = conn.cursor()
        
        sql = """
        WITH LatestInvoices AS (
            SELECT 
                *,
                ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY issue_date DESC) as rn
            FROM invoices
        )
        SELECT 
            c.name, 
            c.phone,
            c.address,
            (SELECT COUNT(*) FROM invoice_items ii WHERE ii.invoice_id = li.id) as item_count,
            li.total_amount,
            li.status
        FROM customers c
        LEFT JOIN LatestInvoices li ON li.customer_id = c.id AND li.rn = 1
        """
        
        params = []
        if search_query:
            sql += " WHERE c.name LIKE ? OR c.phone LIKE ?"
            params = [f"%{search_query}%", f"%{search_query}%"]
            
        sql += " ORDER BY c.name ASC"
        
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        return rows

    @staticmethod
    def get_customers_summary_by_ids(invoice_ids):
        """Returns customer info for a specific list of invoice IDs."""
        if not invoice_ids:
            return []
            
        conn = get_connection()
        cursor = conn.cursor()
        
        placeholders = ",".join(["?"] * len(invoice_ids))
        sql = f"""
        SELECT 
            c.name, 
            c.phone, 
            (SELECT COUNT(*) FROM invoice_items ii WHERE ii.invoice_id = i.id) as item_count,
            i.total_amount,
            i.status
        FROM invoices i
        JOIN customers c ON i.customer_id = c.id
        WHERE i.id IN ({placeholders})
        ORDER BY c.name ASC
        """
        
        cursor.execute(sql, invoice_ids)
        rows = cursor.fetchall()
        return rows

    @staticmethod
    def upsert_customer(name, phone, address=None):
        """
        Creates or finds a customer by name + phone.
        If found, updates phone/address if better values are provided.
        """
        conn = get_connection()
        cursor = conn.cursor()

        name    = str(name).strip().title()    if name    else "Unknown"
        phone   = str(phone).strip()           if phone   else ""
        address = str(address).strip()         if address and str(address).strip() not in ('', 'nan', 'None') else None

        # First try exact name+phone match
        cursor.execute(
            "SELECT id, address FROM customers WHERE LOWER(name) = LOWER(?) AND phone = ?",
            (name, phone)
        )
        result = cursor.fetchone()

        if result:
            customer_id      = result[0]
            existing_address = result[1]
            new_address = address if address else existing_address
            if new_address != existing_address:
                cursor.execute(
                    "UPDATE customers SET address = ? WHERE id = ?",
                    (new_address, customer_id)
                )
        else:
            # If no phone was given, try matching by name only so we don't create empty-phone duplicates
            if not phone:
                cursor.execute(
                    "SELECT id, phone, address FROM customers WHERE LOWER(name) = LOWER(?)",
                    (name,)
                )
                fallback = cursor.fetchone()
                if fallback:
                    customer_id      = fallback[0]
                    existing_address = fallback[2]
                    new_address = address if address else existing_address
                    if new_address != existing_address:
                        cursor.execute(
                            "UPDATE customers SET address = ? WHERE id = ?",
                            (new_address, customer_id)
                        )
                    conn.commit()
                    return customer_id

            cursor.execute(
                "INSERT INTO customers (name, phone, address) VALUES (?, ?, ?)",
                (name, phone, address)
            )
            customer_id = cursor.lastrowid

        conn.commit()
        return customer_id

    @staticmethod
    def merge_duplicate_customers():
        """
        Finds customers with the same name and merges them into one record.
        Invoices are re-pointed to the surviving (oldest) customer ID.
        Returns number of duplicates removed.
        """
        conn = get_connection()
        cursor = conn.cursor()
        removed = 0
        try:
            # Find names with more than one record
            cursor.execute("""
                SELECT LOWER(name) as lname, COUNT(*) as cnt
                FROM customers
                GROUP BY LOWER(name)
                HAVING cnt > 1
            """)
            dup_names = cursor.fetchall()

            for (lname, _) in dup_names:
                cursor.execute(
                    "SELECT id, phone, address FROM customers WHERE LOWER(name) = ? ORDER BY id ASC",
                    (lname,)
                )
                records = cursor.fetchall()
                if len(records) < 2:
                    continue

                # Keep the first (oldest) record as the canonical one
                keep_id   = records[0][0]
                keep_phone   = next((r[1] for r in records if r[1]), records[0][1])
                keep_address = next((r[2] for r in records if r[2]), records[0][2])

                # Update canonical record with best phone/address
                cursor.execute(
                    "UPDATE customers SET phone = ?, address = ? WHERE id = ?",
                    (keep_phone, keep_address, keep_id)
                )

                # Re-point all invoices from duplicate records to the canonical one
                dup_ids = [r[0] for r in records[1:]]
                for dup_id in dup_ids:
                    cursor.execute(
                        "UPDATE invoices SET customer_id = ? WHERE customer_id = ?",
                        (keep_id, dup_id)
                    )
                    cursor.execute("DELETE FROM customers WHERE id = ?", (dup_id,))
                    removed += 1

            conn.commit()
        finally:
            pass
        return removed

    @staticmethod
    def get_all_master_customers():
        """Returns all basic customer records for management."""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, phone, address FROM customers ORDER BY name ASC")
        rows = cursor.fetchall()
        return rows

    @staticmethod
    def update_customer_info(cust_id, name, phone, address=None):
        """Updates a customer's basic details."""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE customers SET name = ?, phone = ?, address = ? WHERE id = ?", (name, phone, address, cust_id))
        conn.commit()

    @staticmethod
    def get_customer_address(name, phone):
        """Returns the address for a customer by name and phone."""
        conn = get_connection()
        cursor = conn.cursor()
        name = str(name).strip().title() if name else ""
        phone = str(phone).strip() if phone else ""
        cursor.execute("SELECT address FROM customers WHERE LOWER(name) = LOWER(?) AND phone = ?", (name, phone))
        row = cursor.fetchone()
        return row[0] if row else None

    @staticmethod
    def import_customers_bulk(customers):
        """
        Bulk-imports a list of customer dicts: [{'name': ..., 'phone': ..., 'address': ...}]
        Returns (added_count, updated_count, skipped_count).
        """
        conn = get_connection()
        cursor = conn.cursor()
        added = 0
        updated = 0
        skipped = 0
        try:
            for c in customers:
                name = str(c.get('name', '')).strip().title()
                phone = str(c.get('phone', '')).strip()
                address = str(c.get('address', '')).strip()
                
                # Normalize empties
                if phone.lower() in ('nan', 'none', ''):
                    phone = ''
                if address.lower() in ('nan', 'none', ''):
                    address = ''
                
                if not name or name.lower() in ('nan', 'none', 'unknown'):
                    skipped += 1
                    continue
                
                cursor.execute(
                    "SELECT id FROM customers WHERE LOWER(name) = LOWER(?) AND phone = ?",
                    (name, phone)
                )
                row = cursor.fetchone()
                if row:
                    # Update address only if we have a new one
                    if address:
                        cursor.execute("UPDATE customers SET address = ? WHERE id = ?", (address, row[0]))
                    updated += 1
                else:
                    cursor.execute(
                        "INSERT INTO customers (name, phone, address) VALUES (?, ?, ?)",
                        (name, phone, address or None)
                    )
                    added += 1
            conn.commit()
        finally:
            pass
        return added, updated, skipped

    @staticmethod
    def find_phone_by_name(name):
        """Tries to find a phone number for a customer name in the master list."""
        conn = get_connection()
        cursor = conn.cursor()
        name = str(name).strip().title() if name else ""
        # Look for the latest phone number assigned to this name
        cursor.execute("SELECT phone FROM customers WHERE LOWER(name) = LOWER(?) AND phone != '' ORDER BY id DESC LIMIT 1", (name,))
        row = cursor.fetchone()
        return row[0] if row else None

    @staticmethod
    def delete_invoice(invoice_id):
        """Safely deletes an invoice and all its line items."""
        conn = get_connection()
        cursor = conn.cursor()
        try:
            # 1. Delete items first (foreign key constraint)
            cursor.execute("DELETE FROM invoice_items WHERE invoice_id = ?", (invoice_id,))
            # 2. Delete invoice
            cursor.execute("DELETE FROM invoices WHERE id = ?", (invoice_id,))
            conn.commit()
        finally:
            pass

    @staticmethod
    def save_invoice(customer_id, invoice_number, total_amount, items):
        """
        Saves a new invoice and its line items.
        'items' should be a list of dicts: [{'name': 'Apple', 'qty': 2, 'price': 5.0}, ...]
        """
        conn = get_connection()
        cursor = conn.cursor()
        
        try:
            # 1. Create Invoice record (Use INSERT OR IGNORE to prevent fail if duplicate number)
            # Use local time for issue_date
            issue_date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute("""
                INSERT OR IGNORE INTO invoices (invoice_number, customer_id, total_amount, status, issue_date)
                VALUES (?, ?, ?, ?, ?)
            """, (invoice_number, customer_id, total_amount, 'Draft', issue_date))
            
            invoice_id = cursor.lastrowid
            
            # If ignore happened, rowcount is 0 and lastrowid is wrong. Handled:
            if cursor.rowcount == 0:
                cursor.execute("SELECT id FROM invoices WHERE invoice_number = ?", (invoice_number,))
                invoice_id = cursor.fetchone()[0]
                # If it already exists, we skip adding items to avoid duplicates
                return invoice_id
            
            # 2. Add Invoice Items
            for item in items:
                subtotal = item['qty'] * item['price']
                cursor.execute("""
                    INSERT INTO invoice_items (invoice_id, description, quantity, unit_price, subtotal)
                    VALUES (?, ?, ?, ?, ?)
                """, (invoice_id, item['name'], item['qty'], item['price'], subtotal))
            
            # 3. Update customer's last invoice date
            local_now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute("UPDATE customers SET last_invoice_date = ? WHERE id = ?", (local_now, customer_id))
            
            conn.commit()
            return invoice_id
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            pass

    @staticmethod
    def delete_customer_by_id(cust_id):
        """Removes the customer record but preserves their invoices as orphaned records."""
        conn = get_connection()
        cursor = conn.cursor()
        try:
            # 1. Nullify customer_id in invoices to prevent cascading delete and preserve history
            cursor.execute("UPDATE invoices SET customer_id = NULL WHERE customer_id = ?", (cust_id,))
            
            # 2. Delete the customer row
            cursor.execute("DELETE FROM customers WHERE id = ?", (cust_id,))
            
            conn.commit()
        finally:
            pass

    @staticmethod
    def delete_customer_by_details(name, phone):
        """Removes the customer record by name/phone but preserves their invoices."""
        conn = get_connection()
        cursor = conn.cursor()
        try:
            name = str(name).strip().title() if name else "Unknown"
            phone = str(phone).strip() if phone else ""
            
            # 1. Find the customer ID
            cursor.execute("SELECT id FROM customers WHERE LOWER(name) = LOWER(?) AND phone = ?", (name, phone))
            row = cursor.fetchone()
            if not row:
                return
            
            cust_id = row[0]
            
            # 2. Orphan the invoices
            cursor.execute("UPDATE invoices SET customer_id = NULL WHERE customer_id = ?", (cust_id,))
            
            # 3. Delete customer
            cursor.execute("DELETE FROM customers WHERE id = ?", (cust_id,))
            
            conn.commit()
        finally:
            pass

    @staticmethod
    def delete_invoice_by_details(name, phone):
        """Finds the latest invoice for this name/phone pair and deletes it."""
        conn = get_connection()
        cursor = conn.cursor()
        try:
            name = str(name).strip().title() if name else "Unknown"
            phone = str(phone).strip() if phone else ""

            cursor.execute("""
                DELETE FROM invoice_items 
                WHERE invoice_id IN (
                    SELECT i.id FROM invoices i
                    JOIN customers c ON i.customer_id = c.id
                    WHERE LOWER(c.name) = LOWER(?) AND c.phone = ?
                )
            """, (name, phone))
            
            cursor.execute("""
                DELETE FROM invoices 
                WHERE id IN (
                    SELECT i.id FROM invoices i
                    JOIN customers c ON i.customer_id = c.id
                    WHERE LOWER(c.name) = LOWER(?) AND c.phone = ?
                )
            """, (name, phone))

            cursor.execute("DELETE FROM customers WHERE LOWER(name) = LOWER(?) AND phone = ?", (name, phone))
            conn.commit()
        finally:
            pass

    @staticmethod
    def get_latest_invoice_by_details(name, phone):
        """Returns the latest invoice and its items for a specific name and phone."""
        conn = get_connection()
        cursor = conn.cursor()
        
        name = str(name).strip().title() if name else "Unknown"
        phone = str(phone).strip() if phone else ""

        cursor.execute("""
            SELECT i.id, i.invoice_number, i.total_amount, i.status, c.name, i.pdf_path
            FROM invoices i
            JOIN customers c ON i.customer_id = c.id
            WHERE LOWER(c.name) = LOWER(?) AND c.phone = ?
            ORDER BY i.issue_date DESC LIMIT 1
        """, (name, phone))
        invoice = cursor.fetchone()
        
        if not invoice:
            return None, []
            
        invoice_id = invoice[0]
        
        # Get items
        cursor.execute("""
            SELECT description, quantity, unit_price, subtotal
            FROM invoice_items
            WHERE invoice_id = ?
        """, (invoice_id,))
        items = cursor.fetchall()
        return invoice, items

    @staticmethod
    def get_master_products():
        """Returns all standard product names for fuzzy matching."""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT standard_name FROM master_products")
        products = [row[0] for row in cursor.fetchall()]
        return products

    @staticmethod
    def add_master_product(name, price=0.0):
        """Adds a new standard product name to the master list."""
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT OR IGNORE INTO master_products (standard_name, default_price) VALUES (?, ?)", (name, price))
            conn.commit()
        finally:
            pass

    @staticmethod
    def update_invoice_pdf(invoice_id, pdf_path):
        """Updates the PDF path and status of an invoice."""
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE invoices SET pdf_path = ?, status = 'Generated' WHERE id = ?", (pdf_path, invoice_id))
            conn.commit()
        finally:
            pass

    @staticmethod
    def update_invoice_status(invoice_id, status):
        """Updates the status of an invoice (e.g., 'Sent')."""
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE invoices SET status = ? WHERE id = ?", (status, invoice_id))
            conn.commit()
        finally:
            pass

    @staticmethod
    def get_all_pending_invoices():
        """Returns all invoices that are not 'Sent' yet, with full details."""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT i.id, i.invoice_number, i.total_amount, i.status, c.name, c.phone, i.pdf_path
            FROM invoices i
            JOIN customers c ON i.customer_id = c.id
            WHERE i.status != 'Sent'
        """)
        rows = cursor.fetchall()
        
        results = []
        for row in rows:
            inv_id = row[0]
            cursor.execute("SELECT description, quantity, unit_price, subtotal FROM invoice_items WHERE invoice_id = ?", (inv_id,))
            items = cursor.fetchall()
            results.append({
                'invoice': row,
                'items': items
            })
        return results

    @staticmethod
    def get_pending_invoices_by_ids(invoice_ids):
        """Returns pending invoices from a specific list of IDs."""
        if not invoice_ids:
            return []
            
        conn = get_connection()
        cursor = conn.cursor()
        
        placeholders = ",".join(["?"] * len(invoice_ids))
        sql = f"""
            SELECT i.id, i.invoice_number, i.total_amount, i.status, c.name, c.phone, i.pdf_path
            FROM invoices i
            JOIN customers c ON i.customer_id = c.id
            WHERE i.id IN ({placeholders}) AND i.status != 'Sent'
        """
        
        cursor.execute(sql, invoice_ids)
        rows = cursor.fetchall()
        
        results = []
        for row in rows:
            inv_id = row[0]
            cursor.execute("SELECT description, quantity, unit_price, subtotal FROM invoice_items WHERE invoice_id = ?", (inv_id,))
            items = cursor.fetchall()
            results.append({
                'invoice': row,
                'items': items
            })
        return results

    @staticmethod
    def log_import(file_name, customer_count, invoice_count, total_value, invoice_ids=None):
        """Logs a successful import event."""
        conn = get_connection()
        cursor = conn.cursor()
        
        # Use local time instead of DB default (UTC)
        import_date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Convert invoice_ids list to comma-separated string for storage
        ids_str = ",".join(map(str, invoice_ids)) if invoice_ids else ""
        
        cursor.execute("""
            INSERT INTO import_logs (file_name, import_date, customer_count, invoice_count, total_value, invoice_ids)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (file_name, import_date, customer_count, invoice_count, total_value, ids_str))
        conn.commit()

    @staticmethod
    def get_dashboard_stats():
        """Returns key metrics for the dashboard including time-based revenue breakdowns."""
        conn = get_connection()
        cursor = conn.cursor()
        
        # Total revenue (all time, latest invoice per customer)
        cursor.execute("""
            WITH LatestInvoices AS (
                SELECT total_amount,
                       ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY issue_date DESC) as rn
                FROM invoices
            )
            SELECT COALESCE(SUM(total_amount), 0) FROM LatestInvoices WHERE rn = 1
        """)
        total_revenue = cursor.fetchone()[0] or 0.0

        # Revenue in last N days helper
        def _revenue_last_n_days(n):
            cursor.execute("""
                SELECT COALESCE(SUM(total_amount), 0)
                FROM invoices
                WHERE issue_date >= datetime('now', ?)
            """, (f'-{n} days',))
            return cursor.fetchone()[0] or 0.0

        revenue_4d  = _revenue_last_n_days(4)
        revenue_10d = _revenue_last_n_days(10)
        revenue_30d = _revenue_last_n_days(30)

        # Daily revenue series for graph (last 30 days)
        cursor.execute("""
            SELECT DATE(issue_date) as day, SUM(total_amount)
            FROM invoices
            WHERE issue_date >= datetime('now', '-30 days')
            GROUP BY DATE(issue_date)
            ORDER BY day ASC
        """)
        daily_revenue = cursor.fetchall()  # list of (date_str, amount)
        return {
            'revenue': total_revenue,
            'revenue_4d': revenue_4d,
            'revenue_10d': revenue_10d,
            'revenue_30d': revenue_30d,
            'daily_revenue': daily_revenue,
        }

    @staticmethod
    def get_customer_full_details(name, phone):
        """Returns ALL invoices and their items for a given customer name/phone pair."""
        conn = get_connection()
        cursor = conn.cursor()
        
        # 0. Normalize
        name = str(name).strip().title() if name else "Unknown"
        phone = str(phone).strip() if phone else ""

        # Get all invoices for this customer
        cursor.execute("""
            SELECT i.id, i.invoice_number, i.total_amount, i.status, i.issue_date, i.pdf_path
            FROM invoices i
            JOIN customers c ON i.customer_id = c.id
            WHERE LOWER(c.name) = LOWER(?) AND c.phone = ?
            ORDER BY i.issue_date DESC
        """, (name, phone))
        invoices = cursor.fetchall()
        
        result = []
        grand_total = 0.0
        for inv in invoices:
            inv_id = inv[0]
            cursor.execute("""
                SELECT description, quantity, unit_price, subtotal
                FROM invoice_items
                WHERE invoice_id = ?
            """, (inv_id,))
            items = cursor.fetchall()
            grand_total += (inv[2] or 0.0)
            result.append({
                'invoice': inv,
                'items': items
            })
        return result, grand_total

    @staticmethod
    def get_recent_imports(limit=10):
        """Returns latest import events."""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, file_name, import_date, customer_count, invoice_count, total_value, invoice_ids
            FROM import_logs
            ORDER BY import_date DESC
            LIMIT ?
        """, (limit,))
        rows = cursor.fetchall()
        return rows

    @staticmethod
    def delete_import(import_id):
        """Deletes an import log and all associated invoices."""
        conn = get_connection()
        cursor = conn.cursor()
        try:
            # 1. Get the invoice IDs from the log
            cursor.execute("SELECT invoice_ids FROM import_logs WHERE id = ?", (import_id,))
            row = cursor.fetchone()
            if not row:
                return
            
            ids_str = row[0]
            if ids_str:
                invoice_ids = [int(i) for i in ids_str.split(',') if i.strip()]
                if invoice_ids:
                    placeholders = ",".join(["?"] * len(invoice_ids))
                    
                    # Delete items
                    cursor.execute(f"DELETE FROM invoice_items WHERE invoice_id IN ({placeholders})", invoice_ids)
                    
                    # Delete invoices
                    cursor.execute(f"DELETE FROM invoices WHERE id IN ({placeholders})", invoice_ids)
            
            # 2. Delete the log entry
            cursor.execute("DELETE FROM import_logs WHERE id = ?", (import_id,))
            
            conn.commit()
        finally:
            pass

    @staticmethod
    def get_customers_by_import_ids(import_ids):
        """
        Returns unique customers (name, phone, address) from invoices
        linked to the given import log IDs.
        Deduplicates by customer name (case-insensitive).
        """
        if not import_ids:
            return []

        conn = get_connection()
        cursor = conn.cursor()

        # 1. Collect all invoice IDs from the selected import logs
        all_invoice_ids = []
        for imp_id in import_ids:
            cursor.execute("SELECT invoice_ids FROM import_logs WHERE id = ?", (imp_id,))
            row = cursor.fetchone()
            if row and row[0]:
                ids = [int(i) for i in row[0].split(',') if i.strip()]
                all_invoice_ids.extend(ids)

        if not all_invoice_ids:
            return []

        # 2. Get unique customers from those invoices
        placeholders = ",".join(["?"] * len(all_invoice_ids))
        cursor.execute(f"""
            SELECT DISTINCT c.name, c.phone, c.address
            FROM invoices i
            JOIN customers c ON i.customer_id = c.id
            WHERE i.id IN ({placeholders})
            ORDER BY c.name ASC
        """, all_invoice_ids)
        rows = cursor.fetchall()

        # 3. Deduplicate by lowercase name
        seen = set()
        unique = []
        for name, phone, address in rows:
            key = (name or '').strip().lower()
            if key and key not in seen:
                seen.add(key)
                unique.append((name, phone or '', address or ''))

        return unique
