from .connection import get_connection

class DataRepository:
    @staticmethod
    def get_all_customers_summary(search_query=None):
        """Returns customers with info from their ABSOLUTE LATEST invoice."""
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
        conn.close()
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
        conn.close()
        return rows

    @staticmethod
    def upsert_customer(name, phone):
        """Creates a customer or returns the ID based on name and phone pair."""
        conn = get_connection()
        cursor = conn.cursor()
        
        # 1. First, check if customer exists by NAME (regardless of phone)
        # If the user wants to update the phone number globally, we should handle that.
        # However, for now, we keep the name+phone pair for invoice history.
        cursor.execute("SELECT id, phone FROM customers WHERE name = ? AND phone = ?", (name, phone))
        result = cursor.fetchone()
        
        if result:
            customer_id = result[0]
        else:
            cursor.execute("INSERT INTO customers (name, phone) VALUES (?, ?)", (name, phone))
            customer_id = cursor.lastrowid
            
        conn.commit()
        conn.close()
        return customer_id

    @staticmethod
    def get_all_master_customers():
        """Returns all basic customer records for management."""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, phone FROM customers ORDER BY name ASC")
        rows = cursor.fetchall()
        conn.close()
        return rows

    @staticmethod
    def update_customer_info(cust_id, name, phone):
        """Updates a customer's basic details."""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE customers SET name = ?, phone = ? WHERE id = ?", (name, phone, cust_id))
        conn.commit()
        conn.close()

    @staticmethod
    def find_phone_by_name(name):
        """Tries to find a phone number for a customer name in the master list."""
        conn = get_connection()
        cursor = conn.cursor()
        # Look for the latest phone number assigned to this name
        cursor.execute("SELECT phone FROM customers WHERE name = ? AND phone != '' ORDER BY id DESC LIMIT 1", (name,))
        row = cursor.fetchone()
        conn.close()
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
            conn.close()

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
            cursor.execute("""
                INSERT OR IGNORE INTO invoices (invoice_number, customer_id, total_amount, status)
                VALUES (?, ?, ?, ?)
            """, (invoice_number, customer_id, total_amount, 'Draft'))
            
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
            cursor.execute("UPDATE customers SET last_invoice_date = CURRENT_TIMESTAMP WHERE id = ?", (customer_id,))
            
            conn.commit()
            return invoice_id
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    @staticmethod
    def delete_customer_by_details(name, phone):
        """Deletes a customer and ALL their invoices/items from the database."""
        conn = get_connection()
        cursor = conn.cursor()
        try:
            # 1. Find the customer ID
            cursor.execute("SELECT id FROM customers WHERE name = ? AND phone = ?", (name, phone))
            row = cursor.fetchone()
            if not row:
                return
            
            cust_id = row[0]
            
            # 2. Get all invoice IDs for this customer
            cursor.execute("SELECT id FROM invoices WHERE customer_id = ?", (cust_id,))
            inv_ids = [r[0] for r in cursor.fetchall()]
            
            # 3. Delete items for each invoice
            for inv_id in inv_ids:
                cursor.execute("DELETE FROM invoice_items WHERE invoice_id = ?", (inv_id,))
                
            # 4. Delete invoices
            cursor.execute("DELETE FROM invoices WHERE customer_id = ?", (cust_id,))
            
            # 5. Finally delete customer
            cursor.execute("DELETE FROM customers WHERE id = ?", (cust_id,))
            
            conn.commit()
        finally:
            conn.close()

    @staticmethod
    def delete_invoice_by_details(name, phone):
        """Finds the latest invoice for this name/phone pair and deletes it."""
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT i.id 
                FROM invoices i 
                JOIN customers c ON i.customer_id = c.id 
                WHERE c.name = ? AND c.phone = ? 
                ORDER BY i.issue_date DESC LIMIT 1
            """, (name, phone))
            row = cursor.fetchone()
            if row:
                inv_id = row[0]
                cursor.execute("DELETE FROM invoice_items WHERE invoice_id = ?", (inv_id,))
                cursor.execute("DELETE FROM invoices WHERE id = ?", (inv_id,))
                conn.commit()
        finally:
            conn.close()

    @staticmethod
    def get_latest_invoice_by_details(name, phone):
        """Returns the latest invoice and its items for a specific name and phone."""
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT i.id, i.invoice_number, i.total_amount, i.status, c.name, i.pdf_path
            FROM invoices i
            JOIN customers c ON i.customer_id = c.id
            WHERE c.name = ? AND c.phone = ?
            ORDER BY i.issue_date DESC LIMIT 1
        """, (name, phone))
        invoice = cursor.fetchone()
        
        if not invoice:
            conn.close()
            return None, []
            
        invoice_id = invoice[0]
        
        # Get items
        cursor.execute("""
            SELECT description, quantity, unit_price, subtotal
            FROM invoice_items
            WHERE invoice_id = ?
        """, (invoice_id,))
        items = cursor.fetchall()
        
        conn.close()
        return invoice, items

    @staticmethod
    def get_master_products():
        """Returns all standard product names for fuzzy matching."""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT standard_name FROM master_products")
        products = [row[0] for row in cursor.fetchall()]
        conn.close()
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
            conn.close()

    @staticmethod
    def update_invoice_pdf(invoice_id, pdf_path):
        """Updates the PDF path and status of an invoice."""
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE invoices SET pdf_path = ?, status = 'Generated' WHERE id = ?", (pdf_path, invoice_id))
            conn.commit()
        finally:
            conn.close()

    @staticmethod
    def update_invoice_status(invoice_id, status):
        """Updates the status of an invoice (e.g., 'Sent')."""
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE invoices SET status = ? WHERE id = ?", (status, invoice_id))
            conn.commit()
        finally:
            conn.close()

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
            
        conn.close()
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
            
        conn.close()
        return results

    @staticmethod
    def log_import(file_name, customer_count, invoice_count, total_value, invoice_ids=None):
        """Logs a successful import event."""
        conn = get_connection()
        cursor = conn.cursor()
        
        # Convert invoice_ids list to comma-separated string for storage
        ids_str = ",".join(map(str, invoice_ids)) if invoice_ids else ""
        
        cursor.execute("""
            INSERT INTO import_logs (file_name, customer_count, invoice_count, total_value, invoice_ids)
            VALUES (?, ?, ?, ?, ?)
        """, (file_name, customer_count, invoice_count, total_value, ids_str))
        conn.commit()
        conn.close()

    @staticmethod
    def get_dashboard_stats():
        """Returns key metrics for the dashboard based on the LATEST invoice for each customer."""
        conn = get_connection()
        cursor = conn.cursor()
        
        # Use CTE to find only the most recent invoice for every customer
        # This prevents double-counting if the same data was imported multiple times
        latest_sql = """
        WITH LatestInvoices AS (
            SELECT 
                total_amount, 
                status,
                ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY issue_date DESC) as rn
            FROM invoices
        )
        SELECT total_amount, status FROM LatestInvoices WHERE rn = 1
        """
        
        cursor.execute(latest_sql)
        rows = cursor.fetchall()
        
        total_revenue = 0.0
        total_count = 0
        pending_count = 0
        sent_count = 0
        
        for amount, status in rows:
            total_revenue += (amount or 0.0)
            total_count += 1
            if status == 'Sent':
                sent_count += 1
            else:
                pending_count += 1
        
        # Total Customers (Independent check)
        cursor.execute("SELECT COUNT(*) FROM customers")
        customer_count = cursor.fetchone()[0] or 0
        
        conn.close()
        return {
            'revenue': total_revenue,
            'total_invoices': total_count,
            'pending': pending_count,
            'customers': customer_count,
            'sent': sent_count
        }

    @staticmethod
    def get_customer_full_details(name, phone):
        """Returns ALL invoices and their items for a given customer name/phone pair."""
        conn = get_connection()
        cursor = conn.cursor()
        
        # Get all invoices for this customer
        cursor.execute("""
            SELECT i.id, i.invoice_number, i.total_amount, i.status, i.issue_date, i.pdf_path
            FROM invoices i
            JOIN customers c ON i.customer_id = c.id
            WHERE c.name = ? AND c.phone = ?
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
        
        conn.close()
        return result, grand_total

    @staticmethod
    def get_recent_imports(limit=10):
        """Returns latest import events."""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT file_name, import_date, customer_count, invoice_count, total_value, invoice_ids
            FROM import_logs
            ORDER BY import_date DESC
            LIMIT ?
        """, (limit,))
        rows = cursor.fetchall()
        conn.close()
        return rows
