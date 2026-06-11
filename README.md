<!-- PROJECT LOGO -->
<br />
<div align="center">
  <a href="https://github.com/">
    <img src="docs/screenshot/img.png" alt="Logo">
  </a>

<h1 align="center">UON ROBOTICS 3 Fingger Gripper</h1>
  <p align="center">
    ROS2 Library for 3-Finger Gripper Control
  </p>
</div>




<br />

## Features
- ![img1.jpg](docs/screenshot/img1.jpg)
- ![img2.jpg](docs/screenshot/img2.jpg)
- ![img3.jpg](docs/screenshot/img3.jpg)
- <video src="https://private-user-images.githubusercontent.com/49944621/605590380-07b1948e-2d28-418d-a890-adb302585b06.mp4?jwt=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJnaXRodWIuY29tIiwiYXVkIjoicmF3LmdpdGh1YnVzZXJjb250ZW50LmNvbSIsImtleSI6ImtleTUiLCJleHAiOjE3ODEwNzU4NTUsIm5iZiI6MTc4MTA3NTU1NSwicGF0aCI6Ii80OTk0NDYyMS82MDU1OTAzODAtMDdiMTk0OGUtMmQyOC00MThkLWE4OTAtYWRiMzAyNTg1YjA2Lm1wND9YLUFtei1BbGdvcml0aG09QVdTNC1ITUFDLVNIQTI1NiZYLUFtei1DcmVkZW50aWFsPUFLSUFWQ09EWUxTQTUzUFFLNFpBJTJGMjAyNjA2MTAlMkZ1cy1lYXN0LTElMkZzMyUyRmF3czRfcmVxdWVzdCZYLUFtei1EYXRlPTIwMjYwNjEwVDA3MTIzNVomWC1BbXotRXhwaXJlcz0zMDAmWC1BbXotU2lnbmF0dXJlPWQyY2NlM2IzMmMyMDRjY2Y0MTE5MDE1ZGZlMWJmYmU3N2RlNjZmMmVhNWVjNzc2YWVhYzAwMjVhZmE2YTFiZjMmWC1BbXotU2lnbmVkSGVhZGVycz1ob3N0JnJlc3BvbnNlLWNvbnRlbnQtdHlwZT12aWRlbyUyRm1wNCJ9.wmV0DwbEKi1bb9Ol2bLTW9XBxP-4g24OSNlk1mvJHIs" autoplay loop muted playsinline width="100%"></video>
- <video src="https://github.com/user-attachments/assets/eddfbb0b-2732-4cf6-bdb4-88b0fac85b01" autoplay loop muted playsinline width="100%"></video>

<br />

## Installation

> [!IMPORTANT]
> USB 권한 설정을 반드시 해야합니다. 터미널에 다음 명령어를 입력 후 재부팅을 해주세요.\
> `sudo usermod -aG dialout $USER` \
> `sudo chmod 666 /dev/ttyUSB0`

### Virtual Environment
1. 파이썬 가상환경을 생성합니다.
    ```shell
    # 파이썬 가상환경 생성
    python3 -m venv .venv
    ```
   
2. 파이썬 가상환경을 활성화합니다.
    ```shell
    # 파이썬 가상환경 활성화
    source .venv/bin/activate
    ```

### Dependencies

```shell
# 패키지 설치
pip install -r requirements.txt
```


<br />

## Quick Start

### Ping

> [!NOTE]
> 그리퍼의 상태를 확인합니다.

```shell
python scripts/uon_3f_gripper_ping.py 
```

|핑 실행 예시|
|:-------------------------------------:|
| ![ping.png](docs/screenshot/ping.png) |



### Demo
> [!NOTE]
> 그리퍼가 열렸다가 닫혀지는 데모를 실행합니다.

```shell
# 데모 실행
python scripts/uon_3f_gripper_demo.py 
```

|               데모 실행 예시                |
|:-------------------------------------:|
| ![dem1.gif](docs/screenshot/dem1.gif) |

<br />

## Usage

> [!TIP]
> GUI를 이용해 그리퍼를 제어하는 예제도 있습니다!

> [!TIP]
> 그리퍼의 힘을 조절하려면 max_effort값을 조절하세요.
> max_effort값이 높을 수록 힘과 반응성이 높아 집니다. 반대로 작을 수록 반응성은 낮아지지만 딸기 같은 물체를 손상 없이 집을 수 있습니다.


```shell
# gui 실행
python scripts/uon_3f_gripper_ui.py
```

|               GUI 실행 예시               |
|:-------------------------------------:|
| ![img5.gif](docs/screenshot/img5.gif) |


<br />

## Troubleshooting

- 