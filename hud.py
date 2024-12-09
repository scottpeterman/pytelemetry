from PyQt6.QtWidgets import QWidget, QGroupBox
from PyQt6.QtCore import Qt, QMargins
from PyQt6.QtGui import QPainter, QPen, QColor, QFont
from PyQt6.QtCharts import QChart, QValueAxis, QLineSeries


class CyberpunkStyle:
    # Color scheme
    CYAN = "#22D3EE"
    CYAN_DARK = "#0891B2"
    CYAN_DARKER = "#164E63"
    BG_BLACK = "#000000"

    @staticmethod
    def apply_theme(app):
        app.setStyle("Fusion")
        app.setStyleSheet("""
            QMainWindow {
                background-color: #000000;
            }

            QWidget {
                background-color: transparent;
                color: #22D3EE;
                font-family: 'Courier New', monospace;
            }

            QGroupBox {
                border: 1px solid rgba(34, 211, 238, 0.2);
                border-radius: 4px;
                margin-top: 8px;
                padding: 24px 16px 16px 16px;
                background-color: rgba(0, 0, 0, 0.8);
            }

            QGroupBox::title {
                subcontrol-origin: margin;
                left: 16px;
                padding: 0 8px;
                color: #22D3EE;
                font-size: 14px;
                font-weight: bold;
            }

            QLineEdit, QComboBox {
                background-color: transparent;
                border: 1px solid rgba(34, 211, 238, 0.3);
                border-radius: 4px;
                padding: 8px;
                color: #22D3EE;
                selection-background-color: rgba(34, 211, 238, 0.2);
            }

            QPushButton {
                background-color: rgba(8, 145, 178, 0.5);
                border: 1px solid rgba(34, 211, 238, 0.3);
                border-radius: 4px;
                padding: 8px 24px;
                color: #22D3EE;
                font-weight: bold;
            }

            QPushButton:hover {
                background-color: rgba(14, 116, 144, 0.5);
            }

            QTreeWidget, QTreeView {
                background-color: transparent;
                border: 1px solid rgba(34, 211, 238, 0.1);
                border-radius: 4px;
                alternate-background-color: rgba(34, 211, 238, 0.05);
            }

            QTreeWidget::item, QTreeView::item {
                padding: 8px;
                border-bottom: 1px solid rgba(34, 211, 238, 0.05);
            }

            QTreeWidget::item:selected, QTreeView::item:selected {
                background-color: rgba(34, 211, 238, 0.1);
            }

            QHeaderView::section {
                background-color: transparent;
                color: #22D3EE;
                border: none;
                border-bottom: 1px solid rgba(34, 211, 238, 0.2);
                padding: 8px;
                font-weight: bold;
            }

            QTabWidget::pane {
                border: 1px solid rgba(34, 211, 238, 0.2);
                background-color: transparent;
                border-radius: 4px;
            }

            QTabBar::tab {
                background-color: transparent;
                color: #22D3EE;
                border: 1px solid rgba(34, 211, 238, 0.2);
                padding: 8px 16px;
                margin-right: 2px;
            }

            QTabBar::tab:selected {
                background-color: rgba(34, 211, 238, 0.1);
            }

            QScrollBar:vertical {
                border: none;
                background: rgba(0, 0, 0, 0.2);
                width: 8px;
                border-radius: 4px;
                margin: 0;
            }

            QScrollBar::handle:vertical {
                background: rgba(34, 211, 238, 0.3);
                border-radius: 4px;
                min-height: 20px;
            }

            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }

            QLabel {
                color: #22D3EE;
            }

            QChart {
                background-color: transparent;
                border: none;
            }

            QChartView {
                background-color: transparent;
                border: 1px solid rgba(34, 211, 238, 0.1);
                border-radius: 4px;
            }
        """)


class FrameDecorator(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        pen = QPen(QColor(34, 211, 238, 76))
        pen.setWidth(2)
        painter.setPen(pen)

        size = 24
        margin = 0

        def draw_corner(x, y, angle):
            painter.save()
            painter.translate(x, y)
            painter.rotate(angle)
            painter.drawLine(0, 0, size, 0)
            painter.drawLine(0, 0, 0, size)
            painter.restore()

        # Draw all corners
        draw_corner(margin, margin, 0)
        draw_corner(self.width() - margin, margin, 90)
        draw_corner(margin, self.height() - margin, -90)
        draw_corner(self.width() - margin, self.height() - margin, 180)


def setup_chart_style(chart_view):
    """Apply cyberpunk styling to a QChartView instance"""
    chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
    chart_view.setBackgroundBrush(QColor(0, 0, 0, 0))

    chart = chart_view.chart()
    chart.setBackgroundVisible(False)
    chart.setPlotAreaBackgroundVisible(True)
    chart.setBackgroundBrush(QColor(0, 0, 0, 0))
    chart.setPlotAreaBackgroundBrush(QColor(0, 0, 0, 40))
    chart.legend().setVisible(False)

    # Configure margins
    chart.setMargins(QMargins(20, 20, 20, 20))
    chart.layout().setContentsMargins(0, 0, 0, 0)

    # Style axes
    for axis in chart.axes():
        axis.setLabelsColor(QColor(CyberpunkStyle.CYAN))
        axis.setGridLineColor(QColor(CyberpunkStyle.CYAN_DARKER))
        axis.setLinePen(QPen(QColor(CyberpunkStyle.CYAN), 1))
        axis.setGridLinePen(QPen(QColor(CyberpunkStyle.CYAN_DARKER), 1, Qt.PenStyle.DotLine))

        # Configure labels
        font = QFont("Courier New", 8)
        axis.setLabelsFont(font)

        # Remove axis line
        axis.setLineVisible(False)

        # Configure tick marks
        axis.setTickCount(6)
        axis.setMinorTickCount(1)

        if isinstance(axis, QValueAxis):
            if axis.orientation() == Qt.Orientation.Vertical:
                axis.setTitleText("UTILIZATION %")
            else:
                axis.setTitleText("TIME (s)")
            axis.setTitleFont(QFont("Courier New", 9, QFont.Weight.Bold))
            axis.setTitleBrush(QColor(CyberpunkStyle.CYAN))


def apply_hud_styling(window):
    """Apply HUD styling to a window and all its widgets"""
    # Add frame decorators to all group boxes
    for group_box in window.findChildren(QGroupBox):
        decorator = FrameDecorator(group_box)
        decorator.setGeometry(group_box.rect())
        group_box.resizeEvent = lambda event, w=group_box, d=decorator: \
            d.setGeometry(w.rect())

    # Set base font
    window.setFont(QFont("Courier New", 10))

    # Set margins
    window.setContentsMargins(16, 16, 16, 16)

    # Set window title prefix
    if not window.windowTitle().startswith("NETWORK HUD"):
        window.setWindowTitle(f"NETWORK HUD :: {window.windowTitle()}")


def style_series(series):
    """Apply cyberpunk styling to a chart series"""
    pen = QPen(QColor(CyberpunkStyle.CYAN))
    pen.setWidth(2)
    series.setPen(pen)

    if isinstance(series, QLineSeries):
        glow_pen = QPen(QColor(CyberpunkStyle.CYAN))
        glow_pen.setWidth(4)
        glow_pen.setColor(QColor(CyberpunkStyle.CYAN).lighter(150))
        series.setPen(glow_pen)

router_content = '''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 60 41">
  <defs>
    <filter id="glow">
      <feGaussianBlur stdDeviation="0.3" result="coloredBlur"/>
      <feMerge>
        <feMergeNode in="coloredBlur"/>
        <feMergeNode in="SourceGraphic"/>
      </feMerge>
    </filter>
  </defs>
  <g fill="none" stroke="#22D3EE" stroke-width="0.8" filter="url(#glow)">
    <!-- Base cylinder outlines -->
    <path d="M29.137 22.837c16.144 0 29.137-5.119 29.137-11.419S45.281 0 29.137 0 0 5.119 0 11.419s12.994 11.419 29.137 11.419z" opacity="0.4"/>
    <path d="M58.274 11.419c0 6.3-12.994 11.419-29.137 11.419S0 17.719 0 11.419v16.537c0 6.3 12.994 11.419 29.137 11.419s29.137-5.119 29.137-11.419z" opacity="0.4"/>

    <!-- Grid lines -->
    <path d="M14.5 11.419 h43.774" opacity="0.2"/>
    <path d="M29.137 5.419 v16.418" opacity="0.2"/>
    <path d="M43.774 11.419 h-43.774" opacity="0.2"/>

    <!-- Network connections -->
    <path d="M22.448 7.081l2.363 3.544-9.056 1.969 1.969-1.575L3.942 8.656 7.486 5.9l13.388 2.362 1.575-1.181z" stroke-width="1"/>
    <path d="M35.442 15.743L33.473 12.2l8.269-1.969-1.181 1.575 13.388 2.362-3.15 2.363-13.781-2.363-1.575 1.575z" stroke-width="1"/>
    <path d="M30.717 5.113l9.056-2.362.394 3.544-2.363-.394-4.331 3.938-4.331-.787 4.331-3.544-2.756-.394z" stroke-width="1"/>
    <path d="M26.78 19.288l-8.662 1.575-.394-4.331 2.756.787 4.725-4.331 4.331.787-5.119 4.725 2.362.788z" stroke-width="1"/>

    <!-- Corner brackets -->
    <path d="M2 2 h6 M2 2 v6" stroke-width="1"/>
    <path d="M58 2 h-6 M58 2 v6" stroke-width="1"/>
    <path d="M2 39 h6 M2 39 v-6" stroke-width="1"/>
    <path d="M58 39 h-6 M58 39 v-6" stroke-width="1"/>
  </g>
</svg>'''

switch_content = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 77 39">
  <defs>
    <filter id="glow">
      <feGaussianBlur stdDeviation="0.3" result="coloredBlur"/>
      <feMerge>
        <feMergeNode in="coloredBlur"/>
        <feMergeNode in="SourceGraphic"/>
      </feMerge>
    </filter>
  </defs>
  <g fill="none" stroke="#22D3EE" stroke-width="0.8" filter="url(#glow)">
    <!-- Main body outlines -->
    <path d="M57.162 37.094v-18.1H0.894v18.1h56.268z" opacity="0.4"/>
    <path d="M0.5 18.994L23.322 0.5h52.334L56.768 18.994H0.5z" opacity="0.4"/>
    <path d="M57.162 37.881L75.656 17.42V0.5L57.162 18.994v18.887z" opacity="0.4"/>
    
    <!-- Network connection paths -->
    <path d="M33.553 14.272l-1.181.787H18.601l-1.574 1.574-3.935-1.574 7.87-2.361-1.574 1.574h14.166z" stroke-width="1"/>
    <path d="M44.571 7.189L43.39 8.369H29.618l-1.574 1.18-3.935-1.574 7.87-1.967-1.574 1.18h14.166z" stroke-width="1"/>
    <path d="M35.914 11.911l1.18-.787H51.26l1.18-1.574 3.935 1.574-7.476 2.361 1.18-1.574H35.914z" stroke-width="1"/>
    <path d="M43.39 4.828l1.181-.787h13.772l1.574-1.574 3.935 1.967-7.87 1.967 1.574-1.574H43.39z" stroke-width="1"/>
    
    <!-- Grid lines -->
    <path d="M14.5 18.994h42.662" opacity="0.2"/>
    <path d="M28.5 0.5v18.494" opacity="0.2"/>
    <path d="M57.162 18.994L75.656 0.5" opacity="0.2"/>
    
    <!-- Corner brackets -->
    <path d="M2 2h6M2 2v6" stroke-width="1"/>
    <path d="M75 2h-6M75 2v6" stroke-width="1"/>
    <path d="M2 37h6M2 37v-6" stroke-width="1"/>
    <path d="M57 37h-6M57 37v-6" stroke-width="1"/>
  </g>
</svg>'''
def get_router_svg(is_switch=False):
    if not is_switch:
        return router_content
    return switch_content