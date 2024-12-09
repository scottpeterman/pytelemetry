from dataclasses import dataclass
from typing import Any, Dict

from PyQt6.QtCharts import QValueAxis
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont, QPen, QPalette, QLinearGradient
from PyQt6.QtWidgets import QApplication, QVBoxLayout, QTreeWidget, QFrame



@dataclass
class ThemeColors:
    # Even darker core colors
    primary: str = "#08666d"  # Darker cyan for primary elements
    secondary: str = "#043438"  # Darker cyan for secondary
    background: str = "#010203"  # Almost black background
    darker_bg: str = "#000000"  # Pure black
    text: str = "#08666d"  # Matching cyan text
    grid: str = "#043438"  # Darker grid lines
    line: str = "#ffff00"  # Graph lines (yellow)
    border: str = "#08666d"  # Darker cyan border
    success: str = "#08666d"  # Matching cyan for UP status
    error: str = "#ef4444"  # Red for DOWN status

    # Border effect colors
    border_light: str = "rgba(8, 102, 109, 0.4)"  # Lighter border for effects
    corner_gap: str = "#010203"  # Color matching background for corner gaps

    # Transparency values
    panel_bg: str = "rgba(0, 0, 0, 0.98)"  # Nearly opaque black
    scrollbar_bg: str = "rgba(2, 3, 4, 0.5)"  # Very dark semi-transparent
    selected_bg: str = "rgba(8, 102, 109, 0.15)"  # Subtle selection

    # Button states
    button_hover: str = "#064b51"  # Darker hover
    button_pressed: str = "#032d30"  # Darker pressed

    chart_bg: str = "rgba(4, 52, 56, 0.15)"  # Subtle chart background


class ThemeLibrary:
    def __init__(self):
        self.themes = {
            "cyberpunk": self.apply_cyberpunk_palette,
            "retro_green": self.apply_retro_green_palette,
            "retro_amber": self.apply_retro_amber_palette,
            "neon_blue": self.apply_neon_blue_palette
        }

        # Theme colors with consistent darkness levels
        self.chart_colors = {
            "cyberpunk": ThemeColors(),  # Keep original cyberpunk
            "retro_green": ThemeColors(
                primary="#0d3b0d",  # Dark green primary
                secondary="#041504",  # Darker green secondary
                background="#010201",  # Almost black with slight green tint
                darker_bg="#000100",  # Pure black with slight green tint
                text="#00ff00",  # Bright green for text (keep this bright for contrast)
                grid="#0d3b0d",  # Dark green grid
                line="#00ff00",  # Bright green for lines
                button_hover="#0d4b0d",  # Slightly lighter hover
                button_pressed="#083008",  # Darker pressed state
                border="#0d3b0d",  # Dark green border
                success="#00ff00",  # Bright green for success
                error="#ff0000",  # Keep red for error
                border_light="rgba(13, 59, 13, 0.4)",  # Semi-transparent dark green
                corner_gap="#010201",  # Match background
                panel_bg="rgba(1, 2, 1, 0.98)",  # Almost opaque dark
                scrollbar_bg="rgba(0, 1, 0, 0.5)",  # Semi-transparent very dark
                selected_bg="rgba(13, 59, 13, 0.15)",  # Very subtle selection
                chart_bg="rgba(13, 59, 13, 0.15)"  # Subtle chart background
            ),
            "retro_amber": ThemeColors(
                primary="#3b2600",  # Dark amber primary
                secondary="#251700",  # Darker amber secondary
                background="#0c0700",  # Almost black with slight amber tint
                darker_bg="#080400",  # Pure black with slight amber tint
                text="#ffa500",  # Bright amber for text (keep this bright for contrast)
                grid="#3b2600",  # Dark amber grid
                line="#ffa500",  # Bright amber for lines
                button_hover="#4b3000",  # Slightly lighter hover
                button_pressed="#301e00",  # Darker pressed state
                border="#3b2600",  # Dark amber border
                success="#ffa500",  # Bright amber for success
                error="#ff4500",  # Keep orange-red for error
                border_light="rgba(59, 38, 0, 0.4)",  # Semi-transparent dark amber
                corner_gap="#0c0700",  # Match background
                panel_bg="rgba(12, 7, 0, 0.98)",  # Almost opaque dark
                scrollbar_bg="rgba(8, 4, 0, 0.5)",  # Semi-transparent very dark
                selected_bg="rgba(59, 38, 0, 0.15)",  # Very subtle selection
                chart_bg="rgba(59, 38, 0, 0.15)"  # Subtle chart background
            ),
            "neon_blue": ThemeColors(  # Keep original neon_blue as is
                primary="#00FFFF",
                secondary="#00004E",
                background="#00001E",
                darker_bg="#000018",
                text="#00FFFF",
                grid="#00004E",
                line="#FFFFFF",
                button_hover="#000064",
                button_pressed="#000080",
                border="#00FFFF",
                success="#00FFFF",
                error="#FF0000",
                border_light="rgba(0, 255, 255, 0.4)",
                corner_gap="#00001E",
                panel_bg="rgba(0, 0, 30, 0.98)",
                scrollbar_bg="rgba(0, 0, 24, 0.5)",
                selected_bg="rgba(0, 255, 255, 0.15)",
                chart_bg="rgba(0, 0, 78, 0.2)"
            )
        }

    def get_colors(self, theme_name: str) -> Dict[str, str]:
        """Return the color dictionary for the specified theme."""
        if theme_name in self.chart_colors:
            return self.chart_colors[theme_name].__dict__
        else:
            print(f"Colors for theme '{theme_name}' not found, returning default.")
            return self.chart_colors["cyberpunk"].__dict__

    def get_chart_colors(self, theme_name: str) -> Dict[str, str]:
        """Alias for get_colors() for backwards compatibility."""
        return self.get_colors(theme_name)

    def apply_theme(self, widget, theme_name):
        if theme_name in self.themes:
            self.themes[theme_name](widget)
        else:
            print(f"Theme '{theme_name}' not found.")

    def _generate_theme_stylesheet(self, theme):
        """Generate common stylesheet with theme-specific colors"""
        return f"""
            QMainWindow, QWidget {{
                background-color: {theme.background};
                color: {theme.text};
                font-family: "Courier New";
            }}

            QGroupBox {{
                background-color: {theme.panel_bg};
                border: 1px solid {theme.border_light};
                margin-top: 1.5em;
                padding: 15px;
                font-family: "Courier New";
            }}

            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: {theme.text};
                font-family: "Courier New";
                text-transform: uppercase;
                background: {theme.background};
            }}

            QLineEdit {{
                background-color: {theme.darker_bg};
                color: {theme.text};
                border: 1px solid {theme.border_light};
                border-radius: 0;
                padding: 5px;
                font-family: "Courier New";
                selection-background-color: {theme.selected_bg};
            }}

            QLineEdit::placeholder {{
                color: {theme.border_light};
            }}

            QComboBox {{
                background-color: {theme.darker_bg};
                color: {theme.text};
                border: 1px solid {theme.border_light};
                border-radius: 0;
                padding: 5px;
                font-family: "Courier New";
                min-width: 6em;
            }}

            QComboBox::drop-down {{
                border: none;
                background: {theme.darker_bg};
                width: 20px;
            }}

            QComboBox::down-arrow {{
                image: none;
                border: 2px solid {theme.text};
                width: 6px;
                height: 6px;
                border-top: none;
                border-right: none;
                transform: rotate(-45deg);
                margin-right: 5px;
            }}

            QPushButton {{
                background-color: {theme.darker_bg};
                color: {theme.text};
                border: 1px solid {theme.border_light};
                border-radius: 0;
                padding: 5px 15px;
                font-family: "Courier New";
                text-transform: uppercase;
            }}

            QPushButton:hover {{
                background-color: {theme.button_hover};
                border: 1px solid {theme.text};
            }}

            QPushButton:pressed {{
                background-color: {theme.button_pressed};
                border: 1px solid {theme.text};
            }}

            QTreeWidget {{
                background-color: {theme.darker_bg};
                color: {theme.text};
                border: 1px solid {theme.border_light};
                font-family: "Courier New";
                outline: none;
                alternate-background-color: {theme.panel_bg};
            }}

            QTreeWidget::item {{
                padding: 5px;
                border: none;
            }}

            QTreeWidget::item:selected {{
                background-color: {theme.selected_bg};
                color: {theme.text};
            }}

            QTreeWidget::item:hover {{
                background-color: {theme.button_hover};
            }}

            QHeaderView::section {{
                background-color: {theme.darker_bg};
                color: {theme.text};
                border: 1px solid {theme.border_light};
                padding: 5px;
                font-family: "Courier New";
                text-transform: uppercase;
            }}

            QTabWidget {{
                border: none;
            }}

            QTabWidget::pane {{
                border: 1px solid {theme.border_light};
                background: {theme.darker_bg};
            }}

            QTabBar::tab {{
                background-color: {theme.darker_bg};
                color: {theme.text};
                border: 1px solid {theme.border_light};
                border-bottom: none;
                padding: 8px 12px;
                font-family: "Courier New";
                text-transform: uppercase;
                min-width: 80px;
                margin-right: 2px;
            }}

            QTabBar::tab:selected {{
                background-color: {theme.primary};
                color: {theme.darker_bg};
            }}

            QTabBar::tab:hover {{
                background-color: {theme.button_hover};
            }}

            QScrollBar:vertical {{
                background-color: {theme.darker_bg};
                width: 8px;
                margin: 0;
            }}

            QScrollBar::handle:vertical {{
                background: {theme.border_light};
                min-height: 20px;
                border-radius: 4px;
            }}

            QScrollBar::add-line:vertical, 
            QScrollBar::sub-line:vertical {{
                height: 0;
                background: none;
            }}

            QScrollBar::add-page:vertical,
            QScrollBar::sub-page:vertical {{
                background: {theme.darker_bg};
            }}

            QScrollBar:horizontal {{
                background-color: {theme.darker_bg};
                height: 8px;
                margin: 0;
            }}

            QScrollBar::handle:horizontal {{
                background: {theme.border_light};
                min-width: 20px;
                border-radius: 4px;
            }}

            QScrollBar::add-line:horizontal,
            QScrollBar::sub-line:horizontal {{
                width: 0;
                background: none;
            }}

            QScrollBar::add-page:horizontal,
            QScrollBar::sub-page:horizontal {{
                background: {theme.darker_bg};
            }}

            QTextEdit {{
                background-color: {theme.darker_bg};
                color: {theme.text};
                border: 1px solid {theme.border_light};
                font-family: "Courier New";
                padding: 5px;
                selection-background-color: {theme.selected_bg};
            }}

            QLabel {{
                color: {theme.text};
                font-family: "Courier New";
            }}

            QChartView {{
                background: transparent;
                border: 1px solid {theme.border_light};
            }}

            /* Chart Title Styling */
            QChart {{
                title-color: {theme.text};
                title-font: bold 10pt "Courier New";
            }}
        """

    def _apply_theme_common(self, widget, theme_name):
        """Apply common theme elements with specific colors"""
        theme = self.chart_colors[theme_name]
        palette = QPalette()

        # Set palette colors
        palette.setColor(QPalette.ColorRole.Window, QColor(theme.background))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(theme.text))
        palette.setColor(QPalette.ColorRole.Base, QColor(theme.darker_bg))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(theme.secondary))
        palette.setColor(QPalette.ColorRole.Text, QColor(theme.text))
        palette.setColor(QPalette.ColorRole.Button, QColor(theme.darker_bg))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(theme.text))

        # Apply palette
        app = QApplication.instance()
        if app:
            app.setPalette(palette)

        # Apply stylesheet
        widget.setStyleSheet(self._generate_theme_stylesheet(theme))

    def apply_cyberpunk_palette(self, widget):
        self._apply_theme_common(widget, "cyberpunk")

    def apply_retro_green_palette(self, widget):
        self._apply_theme_common(widget, "retro_green")

    def apply_retro_amber_palette(self, widget):
        self._apply_theme_common(widget, "retro_amber")

    def apply_neon_blue_palette(self, widget):
        self._apply_theme_common(widget, "neon_blue")


def update_chart_style(self, chart, theme_name: str, axes=None):
    """Enhanced chart styling with HUD-like grid"""
    colors = self.get_colors(theme_name)

    # Configure chart
    chart.setBackgroundVisible(False)
    chart.setPlotAreaBackgroundVisible(True)
    chart.setBackgroundBrush(QColor(0, 0, 0, 0))
    chart.setPlotAreaBackgroundBrush(QColor(colors['darker_bg']))
    chart.legend().setVisible(False)

    if axes:
        for axis in axes:
            # Grid styling
            grid_pen = QPen(QColor(colors['grid']), 1, Qt.PenStyle.DotLine)
            grid_pen.setDashPattern([1, 4])
            axis.setGridLinePen(grid_pen)
            axis.setGridLineColor(QColor(colors['grid']))

            # Labels styling
            axis.setLabelsColor(QColor(colors['text']))
            font = QFont("Courier New", 8)
            axis.setLabelsFont(font)

            if isinstance(axis, QValueAxis):
                axis.setTickCount(6)
                axis.setMinorTickCount(0)
                title_font = QFont("Courier New", 9, QFont.Weight.Bold)
                axis.setTitleFont(title_font)
                axis.setTitleBrush(QColor(colors['text']))


class LayeredHUDFrame(QFrame):
    def __init__(self, parent=None, theme_manager=None, theme_name="cyberpunk"):
        super().__init__(parent)
        self.theme_manager = theme_manager
        self.theme_name = theme_name
        self.setup_ui()
        if theme_manager:
            self.update_theme_colors()

    def setup_ui(self):
        # Main content layout
        self.content_layout = QVBoxLayout(self)
        self.content_layout.setContentsMargins(25, 25, 25, 25)

        # Create corner lines (bright)
        self.corner_lines = []
        for i in range(8):
            line = QFrame(self)
            if i < 4:  # Horizontal corner pieces
                line.setFrameShape(QFrame.Shape.HLine)
                line.setFixedHeight(1)
            else:  # Vertical corner pieces
                line.setFrameShape(QFrame.Shape.VLine)
                line.setFixedWidth(1)
            self.corner_lines.append(line)

        # Create connecting lines (dim)
        self.connecting_lines = []
        for i in range(4):
            line = QFrame(self)
            if i < 2:  # Horizontal connectors
                line.setFrameShape(QFrame.Shape.HLine)
                line.setFixedHeight(1)
            else:  # Vertical connectors
                line.setFrameShape(QFrame.Shape.VLine)
                line.setFixedWidth(1)
            self.connecting_lines.append(line)

        self.setStyleSheet("background-color: transparent;")

        # Set initial colors (will be overridden if theme_manager is provided)
        self.update_line_colors("#0f969e", "rgba(15, 150, 158, 0.3)")

    def update_theme_colors(self):
        """Update colors based on current theme"""
        if self.theme_manager:
            colors = self.theme_manager.get_colors(self.theme_name)
            bright_color = colors['text']
            # Create a semi-transparent version of the text color for connectors
            # Convert hex to rgb for opacity handling
            if bright_color.startswith('#'):
                r = int(bright_color[1:3], 16)
                g = int(bright_color[3:5], 16)
                b = int(bright_color[5:7], 16)
                dim_color = f"rgba({r}, {g}, {b}, 0.3)"
            else:
                dim_color = f"{bright_color}4D"  # 30% opacity

            self.update_line_colors(bright_color, dim_color)

    def update_line_colors(self, bright_color, dim_color):
        """Update line colors with provided colors"""
        # Update corner lines (bright)
        for line in self.corner_lines:
            line.setStyleSheet(f"background-color: {bright_color};")

        # Update connecting lines (dim)
        for line in self.connecting_lines:
            line.setStyleSheet(f"background-color: {dim_color};")

    def set_theme(self, theme_name):
        """Change the theme of the frame"""
        self.theme_name = theme_name
        self.update_theme_colors()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        w, h = self.width(), self.height()
        corner_length = 20  # Length of bright corner pieces

        # Top-left corner
        self.corner_lines[0].setGeometry(0, 0, corner_length, 1)  # Horizontal
        self.corner_lines[4].setGeometry(0, 0, 1, corner_length)  # Vertical

        # Top-right corner
        self.corner_lines[1].setGeometry(w - corner_length, 0, corner_length, 1)  # Horizontal
        self.corner_lines[5].setGeometry(w - 1, 0, 1, corner_length)  # Vertical

        # Bottom-left corner
        self.corner_lines[2].setGeometry(0, h - 1, corner_length, 1)  # Horizontal
        self.corner_lines[6].setGeometry(0, h - corner_length, 1, corner_length)  # Vertical

        # Bottom-right corner
        self.corner_lines[3].setGeometry(w - corner_length, h - 1, corner_length, 1)  # Horizontal
        self.corner_lines[7].setGeometry(w - 1, h - corner_length, 1, corner_length)  # Vertical

        # Connecting lines (dim)
        # Top
        self.connecting_lines[0].setGeometry(corner_length, 0, w - 2 * corner_length, 1)
        # Bottom
        self.connecting_lines[1].setGeometry(corner_length, h - 1, w - 2 * corner_length, 1)
        # Left
        self.connecting_lines[2].setGeometry(0, corner_length, 1, h - 2 * corner_length)
        # Right
        self.connecting_lines[3].setGeometry(w - 1, corner_length, 1, h - 2 * corner_length)


