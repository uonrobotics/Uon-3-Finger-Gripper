#!/usr/bin/env python3
import rclpy
from dynamixel_sdk import COMM_SUCCESS, PacketHandler, PortHandler
from rclpy.node import Node
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


class DynamixelPingNode(Node):

    def __init__(self):
        super().__init__('dynamixel_ping')

        # 파라미터 선언
        self.declare_parameter('device_name', '/dev/ttyUSB0')
        self.declare_parameter('baudrate', 2000000)
        self.declare_parameter('dxl_id', 0)
        self.declare_parameter('protocol_version', 2.0)

        device_name = self.get_parameter('device_name').value
        baudrate = self.get_parameter('baudrate').value
        dxl_id = self.get_parameter('dxl_id').value
        protocol_version = self.get_parameter('protocol_version').value

        # 연결 시도 정보 테이블 출력
        self.print_connection_summary(
            device_name, baudrate, dxl_id, protocol_version
        )

        port_handler = PortHandler(device_name)
        packet_handler = PacketHandler(protocol_version)

        # 포트 열기
        if not port_handler.openPort():
            console.print(
                f'\n[bold red]❌ 에러:[/bold red] 포트를 열 수 없습니다: [yellow]{device_name}[/yellow]'
            )
            return

        # 보레이트 설정
        if not port_handler.setBaudRate(baudrate):
            console.print(
                f'\n[bold red]❌ 에러:[/bold red] 보레이트 설정 실패: [yellow]{baudrate}[/yellow]'
            )
            port_handler.closePort()
            return

        # 핑(Ping) 테스트 수행
        try:
            with console.status(
                    '[bold green]Dynamixel 장치 응답 대기 중...[/bold green]'
            ):
                model_number, result, error = packet_handler.ping(
                    port_handler, dxl_id
                )

            if result != COMM_SUCCESS:
                error_msg = packet_handler.getTxRxResult(result)
                console.print(
                    Panel(
                        f'[bold red]통신 실패 (Result Code: {result})[/bold red]\n{error_msg}',
                        title='[bold red]통신 에러 (TX/RX Error)[/bold red]',
                        border_style='red',
                    )
                )
            elif error != 0:
                error_msg = packet_handler.getRxPacketError(error)
                console.print(
                    Panel(
                        f'[bold orange3]패킷 에러 발생 (Error Code: {error})[/bold orange3]\n{error_msg}',
                        title='[bold orange3]하드웨어/패킷 에러[/bold orange3]',
                        border_style='orange3',
                    )
                )
            else:
                #  성공
                success_message = (
                    f'✅ [bold green]연결 성공![/bold green]\n\n'
                    f'🆔 [bold cyan]Dynamixel ID :[/bold cyan] {dxl_id}\n'
                    f'🤖 [bold magenta]모델 번호 (Model) :[/bold magenta] {model_number} (0x{model_number:04X})'
                )
                console.print(
                    Panel(
                        success_message,
                        title='[bold green]Ping Response Success[/bold green]',
                        border_style='green',
                        expand=False,
                    )
                )

        finally:
            port_handler.closePort()

    def print_connection_summary(self, dev, baud, dxl_id, protocol):
        """연결 설정을 예쁜 테이블로 출력합니다."""
        table = Table(title='🤖 Dynamixel 연결 설정 정보', title_style='bold magenta')

        table.add_column('설정 항목 (Parameter)', justify='left', style='cyan')
        table.add_column('설정값 (Value)', justify='center', style='green')

        table.add_row('장치 경로 (Device Name)', str(dev))
        table.add_row('통신 속도 (Baudrate)', f'{baud:,} bps')
        table.add_row('타겟 ID (Dynamixel ID)', str(dxl_id))
        table.add_row('프로토콜 버전 (Protocol)', f'{protocol:.1f}')

        console.print(table)
        print()


def main(args=None):
    rclpy.init(args=args)
    node = DynamixelPingNode()
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()