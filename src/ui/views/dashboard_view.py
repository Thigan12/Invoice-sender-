from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QScrollArea, QFrame, QMessageBox, QSizePolicy)
from PySide6.QtCore import Qt, Signal, QPointF, QRect
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QLinearGradient, QFont, QPainterPath, QPixmap
import datetime
import os
import sys
from src.database.repository import DataRepository


class RevenueCard(QFrame):
    """A single revenue stat card showing a label and dollar amount."""
    def __init__(self, title, value, color):
        super().__init__()
        self.color = color
        self.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(30, 41, 59, 0.7), stop:1 rgba(15, 23, 42, 0.9));
                border: 1px solid {color}30;
                border-radius: 16px;
                min-width: 180px;
            }}
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        lbl_title = QLabel(title)
        lbl_title.setStyleSheet("color: #94a3b8; font-size: 13px; font-weight: 600; text-transform: uppercase; background: transparent;")

        self.lbl_value = QLabel(value)
        self.lbl_value.setStyleSheet(f"color: {color}; font-size: 28px; font-weight: 800; margin-top: 4px; background: transparent;")

        layout.addWidget(lbl_title)
        layout.addWidget(self.lbl_value)
        layout.addStretch()


class RevenueChartWidget(QWidget):
    """Custom painted line-chart widget for revenue data with hover tooltips."""
    def __init__(self):
        super().__init__()
        self.data = []          # list of (label_str, amount)
        self.setMinimumHeight(260)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._mode = "daily"
        
        # Interactive features
        self.setMouseTracking(True)
        self.hover_index = -1
        self.points = []

    def set_data(self, data, mode="daily"):
        self.data = data or []
        self._mode = mode
        self.hover_index = -1
        self.update()

    def mouseMoveEvent(self, event):
        if not self.data or not self.points:
            return
        
        pos = event.position()
        found_idx = -1
        min_dist = 20 # distance threshold to show tooltip
        
        for i, pt in enumerate(self.points):
            dist = ((pt.x() - pos.x())**2 + (pt.y() - pos.y())**2)**0.5
            if dist < min_dist:
                found_idx = i
                break
        
        if found_idx != self.hover_index:
            self.hover_index = found_idx
            self.update()

    def leaveEvent(self, event):
        self.hover_index = -1
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        if not self.data:
            painter.setPen(QColor("#475569"))
            painter.setFont(QFont("Segoe UI", 12))
            painter.drawText(self.rect(), Qt.AlignCenter, "No revenue data for this period")
            painter.end()
            return

        w, h = self.width(), self.height()
        pad_l, pad_r, pad_t, pad_b = 70, 25, 30, 50
        chart_w, chart_h = w - pad_l - pad_r, h - pad_t - pad_b

        if chart_w <= 0 or chart_h <= 0:
            painter.end()
            return

        values = [v for _, v in self.data]
        real_max = max(values) if values else 1
        
        # --- Smart Y-Axis Scaling ($500 / $1000 steps) ---
        if real_max <= 1000: step = 200
        elif real_max <= 5000: step = 500
        elif real_max <= 10000: step = 1000
        else: step = 2500
        
        num_steps = int((real_max + step - 1) // step)
        if num_steps < 4: num_steps = 4
        max_val = num_steps * step

        # Draw grid and labels
        painter.setFont(QFont("Segoe UI", 9))
        for i in range(num_steps + 1):
            y = pad_t + chart_h - (i / num_steps) * chart_h
            
            # Line
            painter.setPen(QPen(QColor("#1e293b"), 1 if i > 0 else 2))
            painter.drawLine(int(pad_l), int(y), int(w - pad_r), int(y))
            
            # Label
            val = i * step
            painter.setPen(QColor("#64748b"))
            painter.drawText(5, int(y - 10), pad_l - 15, 20, Qt.AlignRight | Qt.AlignVCenter, f"${val:,.0f}")

        # --- Plot Points ---
        n = len(values)
        self.points = []
        for i, val in enumerate(values):
            x = pad_l + (i / (n - 1 if n > 1 else 1)) * chart_w
            y = pad_t + chart_h - (val / max_val) * chart_h
            self.points.append(QPointF(x, y))

        # Main Line
        if len(self.points) > 1:
            path = QPainterPath()
            path.moveTo(self.points[0])
            for pt in self.points[1:]:
                path.lineTo(pt)
            
            painter.setPen(QPen(QColor("#6366f1"), 3, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
            painter.drawPath(path)

            # Gradient Area under the line
            grad_path = QPainterPath(path)
            grad_path.lineTo(int(self.points[-1].x()), int(pad_t + chart_h))
            grad_path.lineTo(int(self.points[0].x()), int(pad_t + chart_h))
            grad_path.closeSubpath()
            
            grad = QLinearGradient(0, pad_t, 0, pad_t + chart_h)
            grad.setColorAt(0, QColor(99, 102, 241, 40))
            grad.setColorAt(1, QColor(99, 102, 241, 0))
            painter.fillPath(grad_path, grad)

        # Draw Dots
        for i, pt in enumerate(self.points):
            is_hovered = (i == self.hover_index)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor("#818cf8") if not is_hovered else QColor("#ffffff"))
            size = 5 if not is_hovered else 7
            painter.drawEllipse(pt, size, size)

        # --- X-Axis Labels ---
        painter.setPen(QColor("#64748b"))
        for i, (label, _) in enumerate(self.data):
             if n > 12 and i % (n // 6) != 0: continue # Only show ~6 labels if many
             x = self.points[i].x()
             painter.drawText(int(x - 40), int(h - 35), 80, 20, Qt.AlignCenter, label)

        # --- TOOLTIP OVERLAY ---
        if self.hover_index != -1:
            label, val = self.data[self.hover_index]
            pt = self.points[self.hover_index]
            
            tip_text = f"{label}\n${val:,.2f}"
            
            # Simple bubble
            rect = QRect(int(pt.x() - 50), int(pt.y() - 60), 100, 45)
            
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor("#1e293b"))
            painter.drawRoundedRect(rect, 8, 8)
            
            painter.setPen(QColor("#ffffff"))
            painter.setFont(QFont("Segoe UI", 9, QFont.Bold))
            painter.drawText(rect, Qt.AlignCenter, tip_text)

        painter.end()


class ImportHistoryCard(QFrame):
    """A card showing a summary of a single import log."""
    clicked = Signal(list) # Emits the invoice_ids for this import
    deleteRequested = Signal(int) # Emits the import_id

    def __init__(self, import_id, file_name, date_str, cust_count, inv_count, total_val, invoice_ids_str):
        super().__init__()
        self.import_id = import_id
        self.invoice_ids = [int(i) for i in invoice_ids_str.split(',')] if invoice_ids_str else []
        try:
            dt = datetime.datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
        except:
            try: dt = datetime.datetime.fromisoformat(date_str)
            except: dt = datetime.datetime.now()
        
        formatted_date = dt.strftime('%b %d, %Y at %H:%M')
        
        self.setStyleSheet("""
            QFrame {
                background: rgba(30, 41, 59, 0.4);
                border: 1px solid rgba(99, 102, 241, 0.1);
                border-radius: 12px;
            }
            QFrame:hover {
                border-color: rgba(99, 102, 241, 0.4);
                background: rgba(30, 41, 59, 0.6);
            }
        """)
        self.setCursor(Qt.PointingHandCursor)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        
        # Date badge on the left
        date_badge = QFrame()
        date_badge.setFixedSize(56, 56)
        date_badge.setStyleSheet("""
            QFrame {
                background: rgba(99, 102, 241, 0.12);
                border: 1px solid rgba(99, 102, 241, 0.2);
                border-radius: 10px;
            }
        """)
        badge_layout = QVBoxLayout(date_badge)
        badge_layout.setContentsMargins(0, 4, 0, 4)
        badge_layout.setSpacing(0)
        badge_layout.setAlignment(Qt.AlignCenter)

        day_lbl = QLabel(dt.strftime('%d'))
        day_lbl.setAlignment(Qt.AlignCenter)
        day_lbl.setStyleSheet("color: #a5b4fc; font-size: 18px; font-weight: 800; background: transparent; border: none;")
        month_lbl = QLabel(dt.strftime('%b'))
        month_lbl.setAlignment(Qt.AlignCenter)
        month_lbl.setStyleSheet("color: #64748b; font-size: 10px; font-weight: 600; text-transform: uppercase; background: transparent; border: none;")
        badge_layout.addWidget(day_lbl)
        badge_layout.addWidget(month_lbl)

        layout.addWidget(date_badge)
        layout.addSpacing(12)

        info = QVBoxLayout()
        info.setSpacing(2)
        name_lbl = QLabel(file_name)
        name_lbl.setStyleSheet("color: #e2e8f0; font-weight: 700; font-size: 14px; background: transparent;")
        date_lbl = QLabel(formatted_date)
        date_lbl.setStyleSheet("color: #64748b; font-size: 11px; background: transparent;")
        info.addWidget(name_lbl)
        info.addWidget(date_lbl)
        
        safe_val = total_val if total_val is not None else 0.0
        stats_lbl = QLabel(f"{cust_count} Customers  |  {inv_count} Invoices  |  ${safe_val:,.2f}")
        stats_lbl.setStyleSheet("color: #a5b4fc; font-size: 13px; background: transparent;")
        
        self.btn_delete = QPushButton("Delete")
        self.btn_delete.setFixedSize(80, 32)
        self.btn_delete.setCursor(Qt.ArrowCursor)
        self.btn_delete.setStyleSheet("""
            QPushButton {
                background: rgba(239, 68, 68, 0.1);
                border: 1px solid rgba(239, 68, 68, 0.2);
                border-radius: 6px;
                color: #f87171;
                font-size: 12px;
                font-weight: 600;
                padding: 0 10px;
            }
            QPushButton:hover {
                background: #ef4444;
                color: white;
                border-color: #ef4444;
            }
        """)
        self.btn_delete.clicked.connect(lambda: self.deleteRequested.emit(self.import_id))

        layout.addLayout(info)
        layout.addStretch()
        layout.addWidget(stats_lbl)
        layout.addSpacing(12)
        layout.addWidget(self.btn_delete)

    def mousePressEvent(self, event):
        if not self.btn_delete.underMouse():
            self.clicked.emit(self.invoice_ids)
        super().mousePressEvent(event)


class DashboardView(QWidget):
    startImportRequested = Signal()
    viewInvoicesRequested = Signal(list)

    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.refresh_data()

    def setup_ui(self):
        # Make whole page scrollable
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: #0f172a; }")
        
        content = QWidget()
        content.setStyleSheet("background: #0f172a;")
        self.layout = QVBoxLayout(content)
        self.layout.setContentsMargins(30, 30, 30, 30)
        self.layout.setSpacing(25)
        
        # 1. Welcome Header
        header_layout = QHBoxLayout()
        welcome = QVBoxLayout()
        title = QLabel("Dashboard")
        title.setStyleSheet("font-size: 32px; font-weight: 800; color: #f8fafc; background: transparent;")
        subtitle = QLabel("Overview of your invoice activity and imports.")
        subtitle.setStyleSheet("color: #94a3b8; font-size: 14px; background: transparent;")
        welcome.addWidget(title)
        welcome.addWidget(subtitle)
        
        # Dashboard Logo
        from src.utils.paths import get_base_dir
        logo_path = os.path.join(get_base_dir(), "assets", "icons", "logo.png")
        logo_label = QLabel()
        if os.path.exists(logo_path):
            logo_label.setPixmap(QPixmap(logo_path).scaled(60, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            logo_label.setFixedSize(65, 65)
            logo_label.setStyleSheet("background: transparent; border: none;")
        
        header_layout.addWidget(logo_label)
        header_layout.addLayout(welcome)
        
        btn_import = QPushButton("New Import")
        btn_import.setFixedSize(140, 45)
        btn_import.setStyleSheet("""
            QPushButton {
                background: #6366f1;
                border-radius: 10px;
                color: white;
                font-weight: 700;
                font-size: 13px;
            }
            QPushButton:hover { background: #4f46e5; }
        """)
        btn_import.clicked.connect(lambda: self.startImportRequested.emit())
        
        header_layout.addLayout(welcome)
        header_layout.addStretch()
        header_layout.addWidget(btn_import)
        self.layout.addLayout(header_layout)

        # 2. Revenue Cards Row
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(16)
        self.card_4d  = RevenueCard("Last 4 Days", "$0.00", "#4ade80")
        self.card_10d = RevenueCard("Last 10 Days", "$0.00", "#a5b4fc")
        self.card_30d = RevenueCard("Monthly (30d)", "$0.00", "#fbbf24")
        stats_layout.addWidget(self.card_4d)
        stats_layout.addWidget(self.card_10d)
        stats_layout.addWidget(self.card_30d)
        self.layout.addLayout(stats_layout)

        # 3. Revenue Chart Section
        chart_header = QHBoxLayout()
        chart_title = QLabel("Revenue")
        chart_title.setStyleSheet("font-size: 20px; font-weight: 700; color: #f8fafc; background: transparent;")
        chart_header.addWidget(chart_title)
        chart_header.addStretch()

        self.btn_day = QPushButton("Day")
        self.btn_week = QPushButton("Week")
        self.btn_month = QPushButton("Month")
        for btn in (self.btn_day, self.btn_week, self.btn_month):
            btn.setFixedSize(70, 30)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet(self._toggle_style(False))
        self.btn_day.setStyleSheet(self._toggle_style(True))
        self.btn_day.clicked.connect(lambda: self._set_chart_mode("daily"))
        self.btn_week.clicked.connect(lambda: self._set_chart_mode("weekly"))
        self.btn_month.clicked.connect(lambda: self._set_chart_mode("monthly"))

        chart_header.addWidget(self.btn_day)
        chart_header.addWidget(self.btn_week)
        chart_header.addWidget(self.btn_month)
        self.layout.addLayout(chart_header)

        chart_frame = QFrame()
        chart_frame.setStyleSheet("""
            QFrame {
                background: rgba(30, 41, 59, 0.5);
                border: 1px solid rgba(99, 102, 241, 0.12);
                border-radius: 14px;
            }
        """)
        chart_frame_layout = QVBoxLayout(chart_frame)
        chart_frame_layout.setContentsMargins(12, 12, 12, 12)
        self.chart = RevenueChartWidget()
        chart_frame_layout.addWidget(self.chart)
        self.layout.addWidget(chart_frame)

        # 4. Recent Activity Section
        activity_label = QLabel("Recent Excel Imports")
        activity_label.setStyleSheet("font-size: 20px; font-weight: 700; color: #f8fafc; margin-top: 10px; background: transparent;")
        self.layout.addWidget(activity_label)
        
        # History content (no independent scroll area, part of main page)
        self.history_content = QWidget()
        self.history_content.setStyleSheet("background: transparent;")
        self.history_layout = QVBoxLayout(self.history_content)
        self.history_layout.setContentsMargins(0, 0, 0, 0)
        self.history_layout.setSpacing(12)
        self.history_layout.setAlignment(Qt.AlignTop)
        
        self.layout.addWidget(self.history_content)
        self.layout.addStretch() # Push everything up
        
        scroll.setWidget(content)
        main_layout.addWidget(scroll)

    def _toggle_style(self, active):
        if active:
            return "QPushButton { background: #6366f1; border: none; border-radius: 6px; color: white; font-size: 12px; font-weight: 700; }"
        return "QPushButton { background: rgba(51, 65, 85, 0.6); border: 1px solid rgba(99, 102, 241, 0.15); border-radius: 6px; color: #94a3b8; font-size: 12px; font-weight: 600; } QPushButton:hover { background: rgba(99, 102, 241, 0.2); color: #e2e8f0; }"

    def _set_chart_mode(self, mode):
        for btn in (self.btn_day, self.btn_week, self.btn_month):
            btn.setStyleSheet(self._toggle_style(False))
        if mode == "daily": self.btn_day.setStyleSheet(self._toggle_style(True))
        elif mode == "weekly": self.btn_week.setStyleSheet(self._toggle_style(True))
        else: self.btn_month.setStyleSheet(self._toggle_style(True))
        self._update_chart(mode)

    def _update_chart(self, mode):
        if not hasattr(self, '_raw_daily'): return
        raw = self._raw_daily
        if mode == "daily":
            chart_data = []
            for date_str, amount in raw:
                try:
                    dt = datetime.datetime.strptime(date_str, '%Y-%m-%d')
                    label = dt.strftime('%d %b')
                except: label = date_str
                chart_data.append((label, amount or 0))
            self.chart.set_data(chart_data, "daily")
        elif mode == "weekly":
            weeks = {}
            for date_str, amount in raw:
                try:
                    dt = datetime.datetime.strptime(date_str, '%Y-%m-%d')
                    week_label = f"W{dt.strftime('%W')}"
                except: week_label = date_str
                weeks[week_label] = weeks.get(week_label, 0) + (amount or 0)
            chart_data = [(k, v) for k, v in weeks.items()]
            self.chart.set_data(chart_data, "weekly")
        elif mode == "monthly":
            months = {}
            for date_str, amount in raw:
                try:
                    dt = datetime.datetime.strptime(date_str, '%Y-%m-%d')
                    month_label = dt.strftime('%b')
                except: month_label = date_str
                months[month_label] = months.get(month_label, 0) + (amount or 0)
            chart_data = [(k, v) for k, v in months.items()]
            self.chart.set_data(chart_data, "monthly")

    def refresh_data(self):
        try:
            stats = DataRepository.get_dashboard_stats()
            self.card_4d.lbl_value.setText(f"${stats['revenue_4d']:,.2f}")
            self.card_10d.lbl_value.setText(f"${stats['revenue_10d']:,.2f}")
            self.card_30d.lbl_value.setText(f"${stats['revenue_30d']:,.2f}")
            self._raw_daily = stats.get('daily_revenue', [])
            self._update_chart("daily")
            
            while self.history_layout.count():
                item = self.history_layout.takeAt(0)
                if item.widget(): item.widget().deleteLater()
                    
            imports = DataRepository.get_recent_imports()
            if not imports:
                no_data = QLabel("No import history yet. Click 'New Import' to get started.")
                no_data.setStyleSheet("color: #64748b; font-style: italic; padding: 40px; border: 1px dashed rgba(99,102,241,0.2); border-radius: 12px; background: transparent;")
                no_data.setAlignment(Qt.AlignCenter)
                self.history_layout.addWidget(no_data)
            else:
                for imp_id, fname, date, c_cnt, i_cnt, val, ids_str in imports:
                    card = ImportHistoryCard(imp_id, fname, date, c_cnt, i_cnt, val, ids_str)
                    card.clicked.connect(self.viewInvoicesRequested.emit)
                    card.deleteRequested.connect(self.on_delete_import)
                    self.history_layout.addWidget(card)
        except Exception as e:
            err_lbl = QLabel(f"Dashboard error: {str(e)}")
            err_lbl.setStyleSheet("color: #f87171; font-style: italic; background: transparent;")
            self.history_layout.addWidget(err_lbl)

    def on_delete_import(self, import_id):
        confirm = QMessageBox(self)
        confirm.setWindowTitle("Confirm Delete")
        confirm.setText("Are you sure you want to delete this import?")
        confirm.setIcon(QMessageBox.Warning)
        confirm.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        confirm.setStyleSheet("QMessageBox { background-color: #1e293b; } QLabel { color: #f8fafc; } QPushButton { background: #334155; border: 1px solid #475569; border-radius: 6px; color: white; padding: 6px 15px; min-width: 80px; }")
        if confirm.exec() == QMessageBox.Yes:
            DataRepository.delete_import(import_id)
            self.refresh_data()
