import ipaddress
import sys
from ipaddress import ip_address, ip_network
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QTabWidget, QTreeWidget, QTreeWidgetItem,
                             QPushButton, QLineEdit, QLabel, QComboBox, QMessageBox,
                             QTextEdit, QScrollArea, QGroupBox, QProgressBar, QFrame, QSizePolicy)
from PyQt6.QtCharts import QChart, QChartView, QLineSeries, QValueAxis
import time
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QMargins, QByteArray
from PyQt6.QtGui import QPixmap, QIcon, QColor, QPen, QPainter, QFont, QPalette
from napalm import get_network_driver
import json
from typing import Dict, Any, Optional, cast
import traceback
from themes import ThemeLibrary,  LayeredHUDFrame

import pynxos
from NetworkInterfacesWidget import NetworkInterfacesWidget
theme_lib = ThemeLibrary()
from tfsm_fire import TextFSMAutoEngine
from hud import (CyberpunkStyle, apply_hud_styling,
                 setup_chart_style, style_series, get_router_svg)
from themes import ThemeLibrary


class CustomDriver:
    def __init__(self, device):
        self.device = device
        self.engine = TextFSMAutoEngine('templates.db')

    def parse_interface_info(self, name, intf, device_type='ios'):
        """
        Parse interface information based on device type
        """
        if device_type == 'ios':
            # Original IOS parsing logic
            protocol_status = intf.get('PROTOCOL_STATUS', '').lower()
            return {
                'is_up': protocol_status == 'up',
                'is_enabled': intf.get('LINK_STATUS', '').lower() == 'up',
                'description': intf.get('DESCRIPTION', ''),
                'mac_address': intf.get('MAC_ADDRESS', ''),
                'speed': float(intf.get('BANDWIDTH', '0').split()[0]) / 1000,
                'mtu': int(intf.get('MTU', 0))
            }

        elif device_type == 'nxos':
            # Nexus parsing based on provided schema
            link_status = intf.get('LINK_STATUS', '').lower()
            admin_state = intf.get('ADMIN_STATE', '').lower()

            # Parse speed from SPEED field (format: '10 Gb/s' or similar)
            speed_str = intf.get('SPEED', '0')
            try:
                if 'Gb/s' in speed_str:
                    speed = float(speed_str.split()[0]) * 1000  # Convert Gb/s to Mb/s
                elif 'Mb/s' in speed_str:
                    speed = float(speed_str.split()[0])
                else:
                    # If auto-speed or other format, get from BANDWIDTH
                    speed = float(intf.get('BANDWIDTH', '0').split()[0]) / 1000
            except (ValueError, IndexError):
                speed = float(intf.get('BANDWIDTH', '0').split()[0]) / 1000

            return {
                'is_up': 'up' in link_status and 'down' not in link_status,
                'is_enabled': admin_state.startswith('up'),
                'description': intf.get('DESCRIPTION', ''),
                'mac_address': intf.get('MAC_ADDRESS', ''),
                'speed': speed,  # In Mbps
                'mtu': int(intf.get('MTU', 0))
            }

        else:
            raise ValueError(f"Unsupported device type: {device_type}")

    def get_interfaces_custom(self):
        """Get interface details using TextFSM parsing."""
        if self.device.platform == "nxos_ssh":
            interface_cmd = "show interface"
        else:
            interface_cmd = "show interfaces"

        output = self.device.cli([interface_cmd])

        if 'eos' in self.device.platform:
            hint = "arista_eos_show_interfaces"
        elif 'nxos' in self.device.platform:
            hint = "cisco_nxos_show_ip_interface"
        else:
            hint = "cisco_ios_show_interfaces"

        template, parsed, score = self.engine.find_best_template(output[interface_cmd], hint)
        print(f"Best template: {interface_cmd}, Score: {score}")
        if score < 5:
            template, parsed, score = self.engine.find_best_template(output[interface_cmd], 'cisco_nxos_show_interface')

        if not parsed:
            return {}, {}

        interfaces = {}
        counters = {}
        print(f"Parsed show interfaces\n{parsed}")
        print(f"reading parsed data")
        print(f"detected driver for parsing: {self.device.platform}")

        try:
            for intf in parsed:
                name = intf['INTERFACE']

                if self.device.platform == "ios":
                    protocol_status = intf.get('PROTOCOL_STATUS', '').split(',')[0].split('(')[0].strip().lower()
                    interfaces[name] = {
                        'is_up': protocol_status == 'up',
                        'is_enabled': intf.get('LINK_STATUS', '').lower() == 'up',
                        'description': intf.get('DESCRIPTION', ''),
                        'mac_address': intf.get('MAC_ADDRESS', ''),
                        'speed': float(intf.get('BANDWIDTH', '0').split()[0]) / 1000,
                        'mtu': int(intf.get('MTU', 0))
                    }

                elif self.device.platform == "nxos_ssh":
                    # Parse LINK_STATUS and ADMIN_STATE for Nexus
                    link_status = intf.get('LINK_STATUS', '').lower()
                    admin_state = intf.get('ADMIN_STATE', '').lower()

                    # Parse speed from SPEED field (format: '10 Gb/s' or 'auto-speed')
                    speed_str = intf.get('SPEED', 'auto-speed')
                    try:
                        if 'Gb/s' in speed_str:
                            speed = float(speed_str.split()[0]) * 1000  # Convert Gb/s to Mb/s
                        elif 'Mb/s' in speed_str:
                            speed = float(speed_str.split()[0])
                        else:
                            # Fall back to BANDWIDTH field if speed is auto or unparseable
                            speed = float(intf.get('BANDWIDTH', '0').split()[0]) / 1000
                    except (ValueError, IndexError):
                        speed = float(intf.get('BANDWIDTH', '0').split()[0]) / 1000

                    interfaces[name] = {
                        'is_up': 'up' in link_status and not any(
                            x in link_status for x in ['down', 'xcvr not inserted', 'administratively down']),
                        'is_enabled': 'up' in admin_state,
                        'description': intf.get('DESCRIPTION', ''),
                        'mac_address': intf.get('MAC_ADDRESS', ''),
                        'speed': speed,
                        'mtu': int(intf.get('MTU', 0))
                    }

                else:
                    # Arista EOS handling
                    protocol_status = intf.get('PROTOCOL_STATUS', '').split(',')[0].split('(')[0].strip().lower()
                    # try:
                    #     bandwidth = float(intf.get('BANDWIDTH', '0').split()[0]) / 1000
                    # except:
                    bandwidth = 1000.0
                    interfaces[name] = {
                        'is_up': protocol_status == 'up',
                        'is_enabled': intf.get('LINK_STATUS', '').lower() == 'up',
                        'description': intf.get('DESCRIPTION', ''),
                        'mac_address': intf.get('MAC_ADDRESS', ''),
                        'speed': bandwidth,
                        'mtu': int(intf.get('MTU', 0))
                    }

                def safe_int(value, default=0):
                    try:
                        return int(value) if value != '' else default
                    except (ValueError, TypeError):
                        return default

                # Handle interface counters
                counters[name] = {
                    'tx_unicast_packets': safe_int(intf.get('OUTPUT_PACKETS', 0)),
                    'rx_unicast_packets': safe_int(intf.get('INPUT_PACKETS', 0)),
                    'tx_errors': safe_int(intf.get('OUTPUT_ERRORS', 0)),
                    'rx_errors': safe_int(intf.get('INPUT_ERRORS', 0)),
                    'tx_discards': 0,  # Not available in current data
                    'rx_discards': 0,  # Not available in current data
                    'tx_rate': float(intf.get('OUTPUT_RATE', 0)),
                    'rx_rate': float(intf.get('INPUT_RATE', 0))
                }

        except Exception as e:
            print(f"Error reading parsed data: {e}")
            traceback.print_exc()

        return interfaces, counters


class DeviceInfoWorker(QThread):
    """Worker thread to handle device operations without blocking the UI"""
    facts_ready = pyqtSignal(object)
    interfaces_ready = pyqtSignal(object)
    neighbors_ready = pyqtSignal(object)
    routes_ready = pyqtSignal(object)
    error = pyqtSignal(str)

    def __init__(self, driver, hostname: str, username: str, password: str):
        super().__init__()
        self.driver = driver
        self.hostname = hostname
        self.username = username
        self.password = password

    def run(self):
        try:
            # Initialize NAPALM driver
            driver = get_network_driver(self.driver)

            optional_args = {}

            # Handle NXOS - switch to SSH if detected
            if self.driver == 'nxos':
                self.driver = 'nxos_ssh'
                optional_args = {
                    'transport': 'ssh',
                    'port': 22
                }
                driver = get_network_driver(self.driver)

            # Handle EOS - force SSH instead of pyeapi
            elif self.driver == 'eos':
                optional_args = {
                    'transport': 'ssh',
                    'use_eapi': False
                }

            # Initialize device with optional arguments
            device = driver(
                hostname=self.hostname,
                username=self.username,
                password=self.password,
                optional_args=optional_args
            )

            device.open()
            self.facts = device.get_facts()


            if "Kernel" in self.facts['hostname']:
                #ios driver on nexus, switch
                device.close()
                driver = get_network_driver('nxos_ssh')
                optional_args = {
                    'transport': 'ssh',
                    'port': 22
                }
                device = driver(
                    hostname=self.hostname,
                    username=self.username,
                    password=self.password,
                    optional_args=optional_args
                )
                device.open()
            self.facts = device.get_facts()
            self.facts_ready.emit(self.facts)
            # Get interface info using custom parser
            custom = CustomDriver(device)
            interfaces, counters = custom.get_interfaces_custom()
            print("\nRaw interface data:")
            print("Interfaces:", json.dumps(interfaces, indent=2))
            print("Counters:", json.dumps(counters, indent=2))
            self.interfaces_ready.emit({"interfaces": interfaces, "counters": counters})

            # Get neighbor info using NAPALM
            lldp = device.get_lldp_neighbors()
            arp = device.get_arp_table()
            self.neighbors_ready.emit({"lldp": lldp, "arp": arp})

            # Get route information
            try:
                # Get raw CLI output for complete routing table
                all_routes_output = device.cli(["show ip route"])

                # Try to get structured route data for default route
                default_route = {}
                try:
                    default_route = device.get_route_to("0.0.0.0/0")
                except:
                    pass  # Some platforms might not support this

                route_info = {
                    "structured_routes": default_route,
                    "raw_output": all_routes_output.get("show ip route", "")
                }
                print(json.dumps(route_info, indent=2))
                self.routes_ready.emit(route_info)

            except Exception as e:
                print(f"Error getting routes: {str(e)}")
                self.routes_ready.emit({})

            device.close()
        except Exception as e:
            self.error.emit(str(e))



class DeviceDashboard(QMainWindow):
    def __init__(self):
        super().__init__()

        # Initialize theme related attributes first
        self.theme_manager = ThemeLibrary()
        self._current_theme = "cyberpunk"  # Set default theme

        # Set window properties
        self.setWindowTitle("Network Device Dashboard")
        self.setGeometry(100, 100, 1400, 900)

        # Initialize interface history tracking
        self.interface_history = {}
        self.history_length = 30  # Store 30 data points

        # Apply theme
        self.theme_manager.apply_theme(self, self._current_theme)

        # Setup the UI
        self.setup_ui()

        # Initialize worker and timer
        self.worker = None
        self.refresh_timer = QTimer()
        self.refresh_timer.setInterval(30000)  # 30 seconds
        self.refresh_timer.timeout.connect(self.refresh_data)
    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Connection settings at top
        conn_group = self.create_connection_group()
        main_layout.addWidget(conn_group)

        # Create main dashboard layout (2x2 grid)
        dashboard_layout = QHBoxLayout()

        # Left side (device info and interfaces)
        left_layout = QVBoxLayout()
        self.device_info_widget = self.create_device_info_widget()
        # self.interfaces_widget = NetworkInterfacesWidget()
        self.interfaces_widget = self.create_interfaces_widget()  # This would use your styled version
        left_layout.addWidget(self.device_info_widget, stretch=2)
        left_layout.addWidget(self.interfaces_widget, stretch=3)

        # Right side (neighbors and optics)
        right_layout = QVBoxLayout()
        self.neighbors_widget = self.create_neighbors_widget()
        # self.optics_widget = self.create_optics_widget()
        self.route_widget = self.create_route_widget()

        right_layout.addWidget(self.neighbors_widget, stretch=1)
        right_layout.addWidget(self.route_widget, stretch=1)

        # Add layouts to main dashboard
        left_container = QWidget()
        left_container.setLayout(left_layout)
        right_container = QWidget()
        right_container.setLayout(right_layout)

        dashboard_layout.addWidget(left_container, stretch=3)
        dashboard_layout.addWidget(right_container, stretch=2)

        main_layout.addLayout(dashboard_layout)

    def create_connection_group(self):
        group = QGroupBox("Device Connection")
        layout = QHBoxLayout()

        self.driver_combo = QComboBox()
        self.driver_combo.addItems(['ios', 'eos', 'nxos'])
        self.hostname_input = QLineEdit()
        self.username_input = QLineEdit()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.connect_button = QPushButton("Connect")
        self.connect_button.clicked.connect(self.connect_device)

        layout.addWidget(QLabel("Driver:"))
        layout.addWidget(self.driver_combo)
        layout.addWidget(QLabel("Hostname:"))
        layout.addWidget(self.hostname_input)
        layout.addWidget(QLabel("Username:"))
        layout.addWidget(self.username_input)
        layout.addWidget(QLabel("Password:"))
        layout.addWidget(self.password_input)
        layout.addWidget(self.connect_button)

        group.setLayout(layout)
        return group


    def create_device_info_widget(self):
        container = LayeredHUDFrame(
            parent=self,
            theme_manager=self.theme_manager,
            theme_name=self._current_theme
        )
        theme_colors = self.theme_manager.get_colors(self._current_theme)

        # Horizontal layout for icon and table
        horizontal_layout = QHBoxLayout()
        horizontal_layout.setSpacing(16)
        horizontal_layout.setContentsMargins(8, 8, 8, 8)

        # SVG Widget
        svg_widget = QSvgWidget()
        svg_widget.setFixedSize(74, 64)
        svg_data = QByteArray(get_router_svg().encode())
        svg_widget.load(svg_data)

        # Store the SVG widget reference for later updates
        self.device_svg = svg_widget

        # Icon container
        svg_container = QWidget()
        svg_layout = QVBoxLayout(svg_container)
        svg_layout.setContentsMargins(0, 0, 0, 0)
        svg_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        svg_layout.addWidget(svg_widget)

        # Device info tree
        self.device_info = QTreeWidget()
        self.device_info.setHeaderLabels(["Property", "Value"])
        self.device_info.setColumnWidth(0, 150)
        self.device_info.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.device_info.setMinimumHeight(200)

        # Style the TreeWidget using theme colors
        self.device_info.setStyleSheet(f"""
            QTreeWidget {{
                background-color: transparent;
                border: none;
                color: {theme_colors['text']};
            }}
            QTreeWidget::item {{
                padding: 5px;
            }}
            QTreeWidget::item:selected {{
                background-color: {theme_colors['selected_bg']};
            }}
            QHeaderView::section {{
                background-color: transparent;
                color: {theme_colors['text']};
                border: none;
                padding: 5px;
                font-family: "Courier New";
                text-transform: uppercase;
            }}
        """)

        # Add widgets to layout
        horizontal_layout.addWidget(svg_container, 1)
        horizontal_layout.addWidget(self.device_info, 3)

        # Add horizontal layout to container
        container.content_layout.addLayout(horizontal_layout)

        return container

    def style_chart(self):
        # Configure chart
        self.chart.setBackgroundVisible(False)
        self.chart.setPlotAreaBackgroundVisible(True)
        self.chart.setBackgroundBrush(QColor(0, 0, 0, 0))
        self.chart.setPlotAreaBackgroundBrush(QColor(22, 78, 99, 40))
        self.chart.legend().setVisible(False)
        self.chart.setMargins(QMargins(20, 20, 20, 20))

        # Style axes
        cyan_color = QColor("#22D3EE")
        dark_cyan = QColor("#164E63")

        for axis in [self.axis_x, self.axis_y]:
            axis.setLabelsColor(cyan_color)
            axis.setGridLineColor(dark_cyan)
            axis.setLinePen(QPen(cyan_color))
            axis.setGridLinePen(QPen(dark_cyan, 1, Qt.PenStyle.DotLine))

            # Configure labels
            font = QFont("Courier New", 8)
            axis.setLabelsFont(font)

            # Configure tick marks
            axis.setTickCount(6)
            axis.setMinorTickCount(1)

            # Set titles
            if isinstance(axis, QValueAxis):
                title_font = QFont("Courier New", 9, QFont.Weight.Bold)
                if axis.orientation() == Qt.Orientation.Vertical:
                    axis.setTitleText("UTILIZATION %")
                else:
                    axis.setTitleText("TIME (s)")
                axis.setTitleFont(title_font)
                axis.setTitleBrush(cyan_color)

    def create_interfaces_widget(self):
        container = LayeredHUDFrame(
            parent=self,
            theme_manager=self.theme_manager,
            theme_name=self._current_theme
        )
        # Split into list and graph sections
        split_layout = QHBoxLayout()
        split_layout.setContentsMargins(8, 8, 8, 8)

        # Interface list
        list_layout = QVBoxLayout()
        self.interfaces_tree = QTreeWidget()
        self.interfaces_tree.setHeaderLabels(["INTERFACE", "STATUS", "UTILIZATION"])
        self.interfaces_tree.setColumnWidth(0, 150)
        self.interfaces_tree.setColumnWidth(1, 80)
        self.interfaces_tree.setColumnWidth(2, 100)
        self.interfaces_tree.itemSelectionChanged.connect(self.update_interface_graph)
        list_layout.addWidget(self.interfaces_tree)

        # Create and configure chart
        self.chart = QChart()
        self.chart_view = QChartView(self.chart)
        self.chart_view.setMinimumHeight(200)
        self.chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Setup chart with theme-aware styling
        self.setup_chart()

        # Add components to layouts
        split_layout.addLayout(list_layout, 1)
        split_layout.addWidget(self.chart_view, 1)

        # Add the split layout to the container
        container.content_layout.addLayout(split_layout)

        return container

    def create_info_box(self, label, value=""):
        box = LayeredHUDFrame()
        box_layout = QVBoxLayout(box)
        box_layout.setSpacing(4)
        box_layout.setContentsMargins(15, 15, 15, 15)  # Adjusted margins to account for frame lines

        label_widget = QLabel(label.upper())
        label_widget.setStyleSheet("""
            color: rgba(34, 211, 238, 0.7);
            font-size: 10px;
            font-weight: bold;
        """)

        value_widget = QLabel(value)
        value_widget.setStyleSheet("""
            color: #22D3EE;
            font-size: 14px;
            font-weight: bold;
        """)

        box_layout.addWidget(label_widget)
        box_layout.addWidget(value_widget)

        box.value_widget = value_widget
        return box

    def create_neighbors_widget(self):
        container = LayeredHUDFrame(
            parent=self,
            theme_manager=self.theme_manager,
            theme_name=self._current_theme
        )
        layout = QVBoxLayout()
        layout.setContentsMargins(8, 8, 8, 8)

        self.neighbors_tabs = QTabWidget()

        # LLDP Tab
        self.lldp_tree = QTreeWidget()
        self.lldp_tree.setHeaderLabels(["Local Port", "Neighbor", "Remote Port"])
        self.neighbors_tabs.addTab(self.lldp_tree, "LLDP")

        # ARP Tab
        self.arp_tree = QTreeWidget()
        self.arp_tree.setHeaderLabels(["IP Address", "MAC Address", "Interface"])
        self.neighbors_tabs.addTab(self.arp_tree, "ARP")

        layout.addWidget(self.neighbors_tabs)
        container.content_layout.addLayout(layout)
        return container
    def connect_device(self):
        # Get connection details
        platform = self.driver_combo.currentText()
        hostname = self.hostname_input.text()
        username = self.username_input.text()
        password = self.password_input.text()

        # Validate input
        if not all([hostname, username, password]):
            QMessageBox.warning(self, "Missing Information",
                                "Please fill in all connection details.")
            return

        # Use appropriate driver based on platform
        if platform in ['nxos']:
            driver = f"{platform}_ssh"  # Force SSH for Nexus and Arista
        else:
            driver = platform

        # Create and start worker thread
        self.worker = DeviceInfoWorker(driver, hostname, username, password)
        self.worker.facts_ready.connect(self.update_device_info)
        self.worker.interfaces_ready.connect(self.update_interfaces)

        self.worker.neighbors_ready.connect(self.update_neighbors)
        # self.worker.routes_ready.connect(self.update)
        self.worker.routes_ready.connect(self.update_routes)  # Make sure this line exists

        self.worker.error.connect(self.handle_error)
        self.worker.start()

        # Start refresh timer
        self.refresh_timer.start()

    def refresh_data(self):
        """Refresh all data from the device"""
        if self.worker and not self.worker.isRunning():
            self.connect_device()

    # def update_device_info(self, facts):
    #     """Update device information with theme awareness"""
    #     theme_colors = self.theme_manager.get_colors(self._current_theme)
    #
    #     # Clear existing items
    #     self.device_info.clear()
    #
    #     # Set device icon based on device type
    #     device_type = facts.get('model', '').lower()
    #
    #     # Update SVG color to match theme - this would require modifying the SVG content
    #     try:
    #         svg_content = get_router_svg()
    #         # Replace the SVG color with theme color
    #         modified_svg = svg_content.replace('#22D3EE', theme_colors['text'])
    #         self.device_svg.load(QByteArray(modified_svg.encode()))
    #     except Exception as e:
    #         print(f"Error updating SVG color: {e}")
    #
    #     # Add facts to tree widget with theme-aware styling
    #     key_facts = [
    #         ('Hostname', facts.get('hostname', 'N/A')),
    #         ('Model', facts.get('model', 'N/A')),
    #         ('is_switch', facts.get('is_switch', 'N/A')),
    #         ('Serial', facts.get('serial_number', 'N/A')),
    #         ('OS Version', facts.get('os_version', 'N/A')),
    #         ('Uptime', str(facts.get('uptime', 'N/A'))),
    #         ('Vendor', facts.get('vendor', 'N/A'))
    #     ]
    #
    #     for key, value in key_facts:
    #         item = QTreeWidgetItem([key, str(value)])
    #         # Set theme-aware colors for the item
    #         item.setForeground(0, QColor(theme_colors['text']))
    #         item.setForeground(1, QColor(theme_colors['text']))
    #         self.device_info.addTopLevelItem(item)

    def update_theme_colors(self):
        """Update colors when theme changes"""
        theme_colors = self.theme_manager.get_colors(self._current_theme)

        # Update TreeWidget styling
        self.device_info.setStyleSheet(f"""
            QTreeWidget {{
                background-color: transparent;
                border: none;
                color: {theme_colors['text']};
            }}
            QTreeWidget::item {{
                padding: 5px;
            }}
            QTreeWidget::item:selected {{
                background-color: {theme_colors['selected_bg']};
            }}
            QHeaderView::section {{
                background-color: transparent;
                color: {theme_colors['text']};
                border: none;
                padding: 5px;
                font-family: "Courier New";
                text-transform: uppercase;
            }}
        """)

        # Update SVG color
        try:
            svg_content = get_router_svg()
            modified_svg = svg_content.replace('#22D3EE', theme_colors['text'])
            self.device_svg.load(QByteArray(modified_svg.encode()))
        except Exception as e:
            print(f"Error updating SVG color: {e}")

        # Update existing items' colors
        root = self.device_info.invisibleRootItem()
        for i in range(root.childCount()):
            item = root.child(i)
            item.setForeground(0, QColor(theme_colors['text']))
            item.setForeground(1, QColor(theme_colors['text']))

    def update_interfaces(self, data):
        """Update interface information in the tree widget"""
        self.interfaces_tree.clear()

        interfaces = data.get('interfaces', {})
        counters = data.get('counters', {})

        for name, details in interfaces.items():
            # Get interface status
            status = "UP" if details.get('is_up') else "DOWN"

            # Calculate utilization from counters if available
            utilization = "0.0%"
            if name in counters:
                counter_data = counters[name]
                # You can modify this calculation based on your needs
                rx_rate = counter_data.get('rx_rate', 0)
                tx_rate = counter_data.get('tx_rate', 0)
                speed = details.get('speed', 1) * 1000000  # Convert to bps
                if speed > 0:
                    utilization = f"{((rx_rate + tx_rate) / speed * 100):.1f}%"

            # Create tree item
            item = QTreeWidgetItem([name, status, utilization])

            # Set item color based on status
            if status == "UP":
                item.setForeground(1, QColor("#22D3EE"))  # Cyan for UP
            else:
                item.setForeground(1, QColor("#EF4444"))  # Red for DOWN

            self.interfaces_tree.addTopLevelItem(item)

        # Sort items by interface name
        self.interfaces_tree.sortItems(0, Qt.SortOrder.AscendingOrder)

    def update_neighbors(self, data):
        # Update LLDP neighbors
        self.lldp_tree.clear()
        for local_port, neighbors in data['lldp'].items():
            for neighbor in neighbors:
                item = QTreeWidgetItem([
                    local_port,
                    neighbor.get('hostname', 'N/A'),
                    neighbor.get('port', 'N/A')
                ])
                self.lldp_tree.addTopLevelItem(item)

        # Update ARP table
        self.arp_tree.clear()
        for entry in data['arp']:
            item = QTreeWidgetItem([
                entry.get('ip', 'N/A'),
                entry.get('mac', 'N/A'),
                entry.get('interface', 'N/A')
            ])
            self.arp_tree.addTopLevelItem(item)

    def handle_error(self, error_msg):
        QMessageBox.critical(
            self,
            "Connection Error",
            f"Error connecting to device:\n{error_msg}"
        )
        self.refresh_timer.stop()

    def get_colors(self, theme_name: str) -> Dict[str, str]:
        """Return the color dictionary for the specified theme."""
        if theme_name in self.chart_colors:
            return self.chart_colors[theme_name].__dict__
        else:
            print(f"Colors for theme '{theme_name}' not found, returning default.")
            return self.chart_colors["cyberpunk"].__dict__

    def apply_theme(self, widget, theme_name):
        if theme_name in self.themes:
            self.themes[theme_name](widget)
        else:
            print(f"Theme '{theme_name}' not found.")
    def get_chart_colors(self, theme_name: str) -> Dict[str, str]:
        """Alias for get_colors() for backwards compatibility."""
        return self.get_colors(theme_name)

    def change_theme(self, theme_name: str):
        """Method to change theme during runtime"""
        self._current_theme = theme_name
        self.theme_manager.apply_theme(self, theme_name)
        # Refresh chart styling with new theme
        self.setup_chart()
    def setup_chart(self):
        """Configure chart with theme-aware styling"""
        theme_colors = self.theme_manager.get_colors(self._current_theme)

        # Basic chart configuration
        self.chart.setBackgroundVisible(False)
        self.chart.setPlotAreaBackgroundVisible(True)
        self.chart.setBackgroundBrush(QColor(0, 0, 0, 0))
        self.chart.setPlotAreaBackgroundBrush(QColor(theme_colors['chart_bg']))
        self.chart.legend().setVisible(False)
        self.chart.setMargins(QMargins(20, 20, 20, 20))

        # Create and configure axes
        self.axis_x = QValueAxis()
        self.axis_y = QValueAxis()

        # Configure axes
        for axis in [self.axis_x, self.axis_y]:
            axis.setLabelsColor(QColor(theme_colors['text']))
            axis.setGridLineColor(QColor(theme_colors['grid']))
            axis.setLinePen(QPen(QColor(theme_colors['text'])))
            axis.setGridLinePen(QPen(QColor(theme_colors['grid']), 1, Qt.PenStyle.DotLine))
            axis.setTickCount(6)
            axis.setMinorTickCount(1)
            axis.setLabelsFont(QFont("Courier New", 8))

            if isinstance(axis, QValueAxis):
                title_font = QFont("Courier New", 9, QFont.Weight.Bold)
                axis.setTitleFont(title_font)
                axis.setTitleBrush(QColor(theme_colors['text']))

        # Configure specific axis properties
        self.axis_x.setRange(0, 300)
        self.axis_x.setTitleText("TIME (s)")

        self.axis_y.setRange(0, 100)
        self.axis_y.setTitleText("UTILIZATION %")

        # Add axes to chart
        self.chart.addAxis(self.axis_x, Qt.AlignmentFlag.AlignBottom)
        self.chart.addAxis(self.axis_y, Qt.AlignmentFlag.AlignLeft)

    def update_interface_graph(self):
        """Update the interface utilization graph for the selected interface"""
        selected_items = self.interfaces_tree.selectedItems()
        if not selected_items:
            return

        interface_name = selected_items[0].text(0)

        # Create new series
        series = QLineSeries()
        series.setName(interface_name)

        # Add sample data points (you would replace this with real data)
        for i in range(30):
            series.append(i * 10, 50 + 30 * (0.5 - (i % 2)))

        # Style the series with a bright yellow color
        pen = QPen(QColor("#FFFF00"))  # Bright yellow
        pen.setWidth(1)  # Line thickness
        series.setPen(pen)

        # Clear and update chart
        self.chart.removeAllSeries()
        self.chart.addSeries(series)
        series.attachAxis(self.axis_x)
        series.attachAxis(self.axis_y)

        # Update chart title
        self.chart.setTitle(f"INTERFACE :: {interface_name}")
        self.chart.setTitleFont(QFont("Courier New", 10, QFont.Weight.Bold))
        self.chart.setTitleBrush(QColor("#22D3EE"))  # Cyan for the title

    def create_route_widget(self):
        container = LayeredHUDFrame(
            parent=self,
            theme_manager=self.theme_manager,
            theme_name=self._current_theme
        )
        layout = QVBoxLayout()
        layout.setContentsMargins(8, 8, 8, 8)

        # Add search box at top
        search_layout = QHBoxLayout()
        self.route_search = QLineEdit()
        self.route_search.setPlaceholderText("Enter IP address to find longest prefix match")
        search_button = QPushButton("Find Route")
        search_button.clicked.connect(self.find_longest_prefix_match)

        search_layout.addWidget(self.route_search)
        search_layout.addWidget(search_button)
        layout.addLayout(search_layout)

        # Create tabs widget
        self.route_tabs = QTabWidget()

        # Table View Tab
        table_container = QWidget()
        table_layout = QVBoxLayout(table_container)
        table_layout.setContentsMargins(0, 0, 0, 0)

        self.route_tree = QTreeWidget()
        self.route_tree.setHeaderLabels([
            "Network", "Mask", "Next Hop", "Protocol", "Interface", "Metric"
        ])
        self.route_tree.setColumnWidth(0, 150)
        table_layout.addWidget(self.route_tree)
        self.route_tabs.addTab(table_container, "Table View")

        # Raw Output Tab
        raw_container = QWidget()
        raw_layout = QVBoxLayout(raw_container)
        raw_layout.setContentsMargins(0, 0, 0, 0)

        self.route_raw = QTextEdit()
        self.route_raw.setReadOnly(True)
        self.route_raw.setFont(QFont("Courier New", 10))
        raw_layout.addWidget(self.route_raw)
        self.route_tabs.addTab(raw_container, "Raw Output")

        layout.addWidget(self.route_tabs)
        container.content_layout.addLayout(layout)
        return container
    def find_longest_prefix_match(self):
        """Find the longest prefix match for the entered IP address."""
        try:
            # Get the search IP
            search_ip = ipaddress.ip_address(self.route_search.text().strip())
            best_match = None
            best_prefix_len = -1
            matching_item = None

            # Get all items from the tree
            root = self.route_tree.invisibleRootItem()
            item_count = root.childCount()

            for i in range(item_count):
                item = root.child(i)
                network = item.text(0)  # Network address
                mask = item.text(1)  # Mask

                try:
                    # Create network object
                    network_obj = ipaddress.ip_network(f"{network}/{mask}")

                    # Check if IP is in this network
                    if search_ip in network_obj:
                        # Check if this is the longest prefix so far
                        prefix_len = network_obj.prefixlen
                        if prefix_len > best_prefix_len:
                            best_prefix_len = prefix_len
                            best_match = network_obj
                            matching_item = item
                except ValueError:
                    continue

            # Highlight the matching route if found
            if matching_item:
                # Clear previous selections
                for i in range(item_count):
                    self.route_tree.invisibleRootItem().child(i).setBackground(0, QColor(0, 0, 0, 0))

                # Highlight the matching route
                matching_item.setBackground(0, QColor("#22D3EE", alpha=40))  # Semi-transparent cyan
                self.route_tree.scrollToItem(matching_item)

                # Show info message
                QMessageBox.information(
                    self,
                    "Route Found",
                    f"Found matching route:\nNetwork: {best_match}\n"
                    f"Next Hop: {matching_item.text(2)}\n"
                    f"Interface: {matching_item.text(4)}"
                )
            else:
                QMessageBox.warning(
                    self,
                    "No Route Found",
                    f"No matching route found for IP: {search_ip}"
                )

        except ValueError as e:
            QMessageBox.warning(
                self,
                "Invalid IP",
                f"Please enter a valid IP address.\nError: {str(e)}"
            )

    def update_routes(self, route_info):
        """Update the routing information display."""
        print("Updating routes with info received")
        self.route_tree.clear()

        try:
            # First add structured routes (usually default route)
            structured_routes = route_info.get("structured_routes", {})
            for prefix, routes in structured_routes.items():
                for route in routes:
                    network, mask = prefix.split('/')
                    item = QTreeWidgetItem([
                        network,
                        mask,
                        route.get('next_hop', ''),
                        route.get('protocol', ''),
                        route.get('outgoing_interface', ''),
                        str(route.get('preference', ''))
                    ])
                    self.route_tree.addTopLevelItem(item)

            # Parse raw output
            raw_output = route_info.get("raw_output", "")
            self.route_raw.setText(raw_output)

            lines = raw_output.split('\n')
            current_network = None
            current_mask = None

            for line in lines:
                line = line.strip()
                if not line:
                    continue

                # Skip header lines
                if line.startswith('Codes:') or line.startswith('Gateway of'):
                    continue

                # Check for subnet information line
                if 'is subnetted' in line:
                    parts = line.split()
                    current_network = parts[0]
                    continue

                # Parse route entries
                if any(line.startswith(code) for code in ['C', 'L', 'S', 'D', 'O', 'B', '*']):
                    try:
                        parts = line.split()
                        protocol = parts[0].replace('*', '')

                        # Handle different line formats
                        if 'via' in line:
                            # Route with next-hop
                            prefix = parts[1]
                            if '/' not in prefix and current_network:
                                # Use subnet from 'is subnetted' line
                                network = prefix
                                mask = current_mask
                            else:
                                network, mask = prefix.split('/')

                            next_hop = parts[parts.index('via') + 1].rstrip(',')
                            interface = parts[-1] if 'Ethernet' in parts[-1] or 'Loopback' in parts[-1] else ''

                            metric = ''
                            if '[' in line and ']' in line:
                                metric = line[line.index('[') + 1:line.index(']')]

                        else:
                            # Directly connected route
                            if 'is directly connected' in line:
                                network, mask = parts[1].split('/')
                                next_hop = 'directly connected'
                                interface = parts[-1]
                                metric = ''
                            else:
                                continue

                        item = QTreeWidgetItem([
                            network,
                            mask,
                            next_hop,
                            protocol,
                            interface,
                            metric
                        ])

                        # Color coding
                        if protocol in ['C', 'L']:
                            item.setForeground(0, QColor("#22D3EE"))  # Cyan for connected
                        elif protocol == 'S':
                            item.setForeground(0, QColor("#10B981"))  # Green for static
                        elif protocol == 'D':
                            item.setForeground(0, QColor("#3B82F6"))  # Blue for EIGRP
                        elif protocol == 'O':
                            item.setForeground(0, QColor("#F59E0B"))  # Amber for OSPF

                        self.route_tree.addTopLevelItem(item)

                    except Exception as e:
                        print(f"Error parsing line: {line}, Error: {str(e)}")

            # Adjust column widths
            for i in range(self.route_tree.columnCount()):
                self.route_tree.resizeColumnToContents(i)

        except Exception as e:
            print(f"Error updating routes: {str(e)}")
            QMessageBox.warning(
                self,
                "Route Update Error",
                f"Error updating route information: {str(e)}"
            )

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = DeviceDashboard()
    window.show()
    sys.exit(app.exec())