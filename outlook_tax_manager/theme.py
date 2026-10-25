"""
Theme stylesheet definition for Outlook Email Tax Manager
Color palette modeled after the Blue & White E-Government / Tax Services Portal (dichvucong.gdt.gov.vn)
- Primary Navy / Ocean Blue: #0F4C81 / #0A4B88 / #1B365D
- Secondary Cyan / Light Blue Accent: #0078D4 / #00A8E8 / #E6F0FA
- Main Background: Clean Soft Ice Blue (#F4F7FA) / Cards: Crisp White (#FFFFFF)
"""

TAX_THEME_QSS = """
QMainWindow {
    background-color: #F4F7FA;
    font-family: 'Segoe UI', Tahoma, Arial, sans-serif;
}

QWidget {
    font-family: 'Segoe UI', Tahoma, Arial, sans-serif;
    color: #2D3748;
}

/* Header Banner Styling - Blue & White Government Tax Portal */
#headerBanner {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0B2545, stop:0.4 #0F4C81, stop:0.8 #0A4B88, stop:1 #13293D);
    border-bottom: 4px solid #00A8E8;
    min-height: 75px;
    max-height: 75px;
}

#headerTitle {
    color: #FFFFFF;
    font-size: 21px;
    font-weight: 800;
    letter-spacing: 0.5px;
}

#headerSubtitle {
    color: #E0F2FE;
    font-size: 12px;
    font-weight: 500;
}

/* Sidebar Navigation - Dark Navy Blue */
#sidebar {
    background-color: #0B192C;
    border-right: 1px solid #1E3E62;
    min-width: 240px;
    max-width: 240px;
}

#sidebar QPushButton {
    background-color: transparent;
    color: #E2E8F0;
    text-align: left;
    padding: 13px 20px;
    font-size: 14px;
    font-weight: 600;
    border: none;
    border-left: 5px solid transparent;
    border-radius: 0px;
}

#sidebar QPushButton:hover {
    background-color: #1E3E62;
    color: #38BDF8;
    border-left: 5px solid #00A8E8;
}

#sidebar QPushButton:checked {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0F4C81, stop:1 #0284C7);
    color: #FFFFFF;
    border-left: 5px solid #38BDF8;
    font-weight: bold;
}

/* Cards & Containers */
QFrame.card {
    background-color: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-top: 3px solid #0F4C81;
    border-radius: 8px;
    padding: 16px;
}

QLabel.cardTitle {
    font-size: 15px;
    font-weight: bold;
    color: #0F4C81;
    border-bottom: 2px solid #38BDF8;
    padding-bottom: 6px;
    margin-bottom: 10px;
}

QLabel.metricValue {
    font-size: 28px;
    font-weight: bold;
    color: #0F172A;
}

QLabel.metricLabel {
    font-size: 12px;
    color: #64748B;
    font-weight: 600;
    text-transform: uppercase;
}

/* GroupBox Container */
QGroupBox {
    background-color: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-top: 3px solid #0F4C81;
    border-radius: 8px;
    font-weight: bold;
    font-size: 14px;
    color: #0F4C81;
    margin-top: 12px;
    padding-top: 14px;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 2px 10px;
    background-color: #FFFFFF;
    color: #0F4C81;
}

/* Progress Bar */
QProgressBar {
    border: 1px solid #CBD5E0;
    border-radius: 6px;
    text-align: center;
    background-color: #F1F5F9;
    font-weight: bold;
    height: 24px;
    color: #0F172A;
}

QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0284C7, stop:0.7 #0F4C81, stop:1 #1E3A8A);
    border-radius: 5px;
}

/* Buttons */
QPushButton.btnPrimary {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #0284C7, stop:1 #0F4C81);
    color: #FFFFFF;
    border: 1px solid #0369A1;
    border-radius: 6px;
    padding: 9px 18px;
    font-weight: bold;
    font-size: 13px;
}

QPushButton.btnPrimary:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #38BDF8, stop:1 #0284C7);
    border-color: #38BDF8;
}

QPushButton.btnPrimary:pressed {
    background-color: #0369A1;
}

QPushButton.btnGold {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #F59E0B, stop:1 #D97706);
    color: #FFFFFF;
    border: 1px solid #B45309;
    border-radius: 6px;
    padding: 9px 18px;
    font-weight: bold;
    font-size: 13px;
}

QPushButton.btnGold:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #FBBF24, stop:1 #F59E0B);
}

QPushButton.btnDanger {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #EF4444, stop:1 #DC2626);
    color: #FFFFFF;
    border: 1px solid #B91C1C;
    border-radius: 6px;
    padding: 9px 18px;
    font-weight: bold;
    font-size: 13px;
}

QPushButton.btnDanger:hover {
    background-color: #F87171;
}

QPushButton.btnSecondary {
    background-color: #F1F5F9;
    color: #1E293B;
    border: 1px solid #CBD5E0;
    border-radius: 6px;
    padding: 9px 18px;
    font-weight: 600;
    font-size: 13px;
}

QPushButton.btnSecondary:hover {
    background-color: #E2E8F0;
}

/* Tables */
QTableWidget {
    background-color: #FFFFFF;
    border: 1px solid #E2E8F0;
    gridline-color: #F1F5F9;
    border-radius: 6px;
    selection-background-color: #E0F2FE;
    selection-color: #0F4C81;
}

QHeaderView::section {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #0F4C81, stop:1 #0A3663);
    color: #FFFFFF;
    padding: 9px;
    font-weight: bold;
    border: none;
    font-size: 13px;
    border-right: 1px solid #0369A1;
}

QTableWidget::item {
    padding: 6px 10px;
}

QTableWidget::item:alternate {
    background-color: #F8FAFC;
}

QLabel {
    font-size: 13px;
    padding: 2px 0px;
}

/* Input Fields - Generous height & minimal padding so descenders (g, y, p, j, q) are never clipped */
QLineEdit, QComboBox, QSpinBox, QTimeEdit {
    background-color: #FFFFFF;
    border: 1px solid #CBD5E0;
    border-radius: 6px;
    padding: 2px 10px;
    min-height: 34px;
    font-size: 13px;
}

QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QTimeEdit:focus {
    border: 2px solid #0284C7;
}

QPushButton {
    background-color: #F8FAFC;
    color: #1E293B;
    border: 1px solid #CBD5E0;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: 600;
    font-size: 13px;
    min-height: 20px;
}

QPushButton:hover {
    background-color: #E2E8F0;
}


/* ScrollBars */
QScrollBar:vertical {
    border: none;
    background: #F1F5F9;
    width: 10px;
    border-radius: 5px;
}

QScrollBar::handle:vertical {
    background: #94A3B8;
    border-radius: 5px;
}

QScrollBar::handle:vertical:hover {
    background: #0284C7;
}

/* Tab Widget */
QTabWidget::pane {
    border: 1px solid #E2E8F0;
    background: #FFFFFF;
    border-radius: 6px;
}

QTabBar::tab {
    background: #F1F5F9;
    color: #475569;
    padding: 9px 18px;
    font-weight: bold;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    margin-right: 3px;
}

QTabBar::tab:selected {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #0284C7, stop:1 #0F4C81);
    color: #FFFFFF;
}
"""
