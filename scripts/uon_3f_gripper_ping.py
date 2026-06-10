#!/usr/bin/env python3
import sys
import argparse
from dynamixel_sdk import COMM_SUCCESS, PacketHandler, PortHandler
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

class DynamixelPing:
    def __init__(self, device_name='/dev/ttyUSB0', baudrate=2000000, dxl_id=0, protocol_version=2.0):
        self.device_name = device_name
        self.baudrate = baudrate
        self.dxl_id = dxl_id
        self.protocol_version = protocol_version

        # 연결 시도 정보 테이블 출력
        self.print_connection_summary()

        self.port_handler = PortHandler(self.device_name)
        self.packet_handler = PacketHandler(self.protocol_version)

        self.run_ping_test()

    def run_ping_test(self):
        # 포트 열기
        if not self.port_handler.openPort():
            console.print(
                f'\n[bold red]❌ 에러:[/bold red] 포트를 열 수 없습니다: [yellow]{self.device_name}[/yellow]'
            )
            return

        # 보레이트 설정
        if not self.port_handler.setBaudRate(self.baudrate):
            console.print(
                f'\n[bold red]❌ 에러:[/bold red] 보레이트 설정 실패: [yellow]{self.baudrate}[/yellow]'
            )
            self.port_handler.closePort()
            return

        # 핑(Ping) 테스트 수행
        try:
            with console.status(
                    '[bold green]Dynamixel 장치 응답 대기 중...[/bold green]'
            ):
                model_number, result, error = self.packet_handler.ping(
                    self.port_handler, self.dxl_id
                )

            if result != COMM_SUCCESS:
                error_msg = self.packet_handler.getTxRxResult(result)
                console.print(
                    Panel(
                        f'[bold red]통신 실패 (Result Code: {result})[/bold red]\n{error_msg}',
                        title='[bold red]통신 에러 (TX/RX Error)[/bold red]',
                        border_style='red',
                    )
                )
            elif error != 0:
                error_msg = self.packet_handler.getRxPacketError(error)
                console.print(
                    Panel(
                        f'[bold orange3]패킷 에러 발생 (Error Code: {error})[/bold orange3]\n{error_msg}',
                        title='[bold orange3]하드웨어/패킷 에러[/bold orange3]',
                        border_style='orange3',
                    )
                )
            else:
                # 성공
                success_message = (
                    f'✅ [bold green]연결 성공![/bold green]\n\n'
                    f'🆔 [bold cyan]Dynamixel ID :[/bold cyan] {self.dxl_id}\n'
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

        except Exception as e:
            console.print(f'[bold red]알 수 없는 에러 발생:[/bold red] {e}')
        finally:
            self.port_handler.closePort()

    def print_connection_summary(self):
        """연결 설정을 예쁜 테이블로 출력합니다."""
        table = Table(title='🤖 Dynamixel 연결 설정 정보', title_style='bold magenta')

        table.add_column('설정 항목 (Parameter)', justify='left', style='cyan')
        table.add_column('설정값 (Value)', justify='center', style='green')

        table.add_row('장치 경로 (Device Name)', str(self.device_name))
        table.add_row('통신 속도 (Baudrate)', f'{self.baudrate:,} bps')
        table.add_row('타겟 ID (Dynamixel ID)', str(self.dxl_id))
        table.add_row('프로토콜 버전 (Protocol)', f'{self.protocol_version:.1f}')

        console.print(table)
        print()

def main():
    parser = argparse.ArgumentParser(description='Dynamixel Ping Test (No ROS2)')
    parser.add_argument('--device', type=str, default='/dev/ttyUSB0', help='Device name (default: /dev/ttyUSB0)')
    parser.add_argument('--baud', type=int, default=2000000, help='Baudrate (default: 2000000)')
    parser.add_argument('--id', type=int, default=0, help='Dynamixel ID (default: 0)')
    parser.add_argument('--protocol', type=float, default=2.0, help='Protocol version (default: 2.0)')

    args = parser.parse_args()

    DynamixelPing(
        device_name=args.device,
        baudrate=args.baud,
        dxl_id=args.id,
        protocol_version=args.protocol
    )

if __name__ == '__main__':
    main()
