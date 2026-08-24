# Danny Capture - 구현 및 수정 프로세스 기록 (2026-06-09)

본 문서는 Danny Capture 프로그램 개발 및 문제 해결 과정에서 진행된 분석, 소스코드 수정, 빌드 및 배포, 그리고 추가 개선 사항에 대해 상세히 기록한 문서입니다.

---

## 1. 개요 및 목적
* **대상 프로그램**: Danny Capture (PySide6 및 `mss` 라이브러리 기반 윈도우 화면 캡처 프로그램)
* **주요 해결 과제**: 캡처 후 클립보드에 복사하거나 파일로 저장할 때, 원본의 파란 형광색(Cyan 계열)이 보색인 노란 형광색(Yellow/Orange 계열)으로 변환되는 색상 왜곡(채널 반전) 문제 해결.
* **추가 목표**: 프로그램 종료 기능 부재에 따른 편의성 문제 개선 및 메모리 안정성, 브랜드 일관성 향상.

---

## 2. 오류 발생 내용 및 상세 분석

### 2.1 색상 왜곡 오류 현상
* **증상**: 파란 형광색(예: RGB `0, 180, 240`)을 화면 캡처하여 클립보드에 붙여넣기 하면 노란 형광색(예: RGB `240, 180, 0`)으로 색상이 반전되어 표시됨.
* **원인 추정**: 캡처 이미지 데이터 로드 및 클립보드 전송 중 Red(R) 채널과 Blue(B) 채널이 서로 뒤바뀌는 현상(RGB ↔ BGR) 발생.

### 2.2 기술적 분석 및 교차 검증 (Scratch 테스트)
정확한 원인 파악을 위해 임시 테스트 스크립트([test_color.py](file:///C:/Users/cho/.gemini/antigravity-ide/brain/d685f381-b6d7-4f89-906e-7fa407cc1097/scratch/test_color.py)) 및 ([test_capture_flow.py](file:///C:/Users/cho/.gemini/antigravity-ide/brain/d685f381-b6d7-4f89-906e-7fa407cc1097/scratch/test_capture_flow.py))를 작성하여 테스트를 진행했습니다.

1. **화면 캡처 엔진 테스트 (`mss` vs PySide6)**
   * PySide6 `QScreen.grabWindow`로 취득한 올바른 색상 데이터: `0, 145, 230` (파란색 계열)
   * `mss` 캡처 데이터에서 `BGRX` 디코더로 로드한 PIL 이미지 데이터: `(0, 145, 230)` (정상)
   * **결론**: `core/capture.py`에서 `mss` 데이터를 로드하는 부분은 정상적으로 RGB 변환이 이루어지고 있음.
2. **클립보드 함수 분석 (`core/clipboard.py`)**
   * 기존 코드에 PIL 이미지 데이터를 QImage 포맷(`Format_RGBA8888`)으로 변환하기 전, 수동으로 R 채널과 B 채널을 쪼개어 바꾸는 코드(`Image.merge("RGB", (b, g, r))`)가 포함되어 있었음.
   * 이 중복 채널 스왑 로직이 최종 클립보드 전송 시에 색상을 거꾸로 뒤집는 범인이었음을 확정함.
3. **업데이트 미반영 문제 분석**
   * 소스코드를 수정하고 작업관리자에서 프로그램을 재시작했음에도 여전히 색상이 반전되는 문제가 관찰됨.
   * 개발 디렉터리 내의 빌드본 수정 일자를 확인한 결과:
     * `DannyCapture_Single.exe` (2026-05-29)
     * `DannyCapture_Setup.exe` (2026-04-24)
     * 실제 사용자 PC에 설치된 경로(`C:\Users\cho\AppData\Local\DannyCapture\DannyCapture_Single.exe`) 파일 역시 **5월 29일 버전**이었음.
   * **결론**: 소스코드만 수정하고 실행 파일(EXE) 및 설치 파일을 새로 빌드하여 설치 경로에 적용하지 않았기 때문에 구버전이 계속 작동하고 있었음.

---

## 3. 오류 수정 및 반영 프로세스

### 3.1 소스코드 수정 (`core/clipboard.py`)
불필요한 수동 채널 스왑 로직을 제거하고, PIL의 RGBA 변환 로직을 일관성 있게 변경했습니다.

* **수정 전**:
  ```python
  if image.mode == "RGB":
      r, g, b = image.split()
      image = Image.merge("RGB", (b, g, r))
  elif image.mode == "RGBA":
      r, g, b, a = image.split()
      image = Image.merge("RGBA", (b, g, r, a))
  ```
* **수정 후**:
  ```python
  # Convert PIL Image to RGBA mode if it isn't already
  if image.mode != "RGBA":
      image = image.convert("RGBA")
  ```

### 3.2 컴파일 및 배포 환경 갱신
1. **PyInstaller 실행 파일 빌드**
   ```powershell
   python -m PyInstaller --clean DannyCapture_Single.spec
   ```
   * 결과물: `dist/DannyCapture_Single.exe` 생성 완료.
2. **Inno Setup 설치 패키지 빌드**
   ```powershell
   & "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss
   ```
   * 결과물: `Output/DannyCapture_Setup.exe` 패키징 완료.
3. **설치 경로 수동 강제 업데이트**
   * 사용자 편의를 위해 `dist/DannyCapture_Single.exe`를 실제 사용자 윈도우 설치 경로(`C:\Users\cho\AppData\Local\DannyCapture\`)에 강제 덮어쓰기하여 즉시 업데이트를 수행함.
   * 이후 단축키 및 시작 메뉴 실행 시 **정상적인 파란 형광색(원본 색상)이 유지됨을 최종 확인**.

---

## 4. 추가 기능 개선 사항 (품질 향상)

프로그램의 사용자 편의성(QoL) 및 안정성을 제고하기 위해 다음과 같은 기능을 추가 개발하여 반영하였습니다.

### 4.1 메인 툴바 우클릭 메뉴 구현 (`ui/main_toolbar.py`)
* **개선 배경**: 메인 툴바는 테두리가 없는 프레임리스 창(`FramelessWindowHint`)이며, `❌` 버튼을 누르면 트레이로만 가려집니다. 별도의 종료 버튼이 없어 프로그램을 종료하려면 작업관리자를 켜야 하는 심각한 사용성 문제가 있었습니다.
* **구현**: 툴바에 우클릭 컨텍스트 메뉴(`contextMenuEvent`)를 추가하였습니다.
  * 마우스 우클릭 시 `⚙️ 환경설정` 및 `❌ 프로그램 종료` 메뉴를 팝업하여 직관적으로 앱을 끌 수 있도록 개선했습니다.

### 4.2 클립보드 메모리 안정성 강화 (`core/clipboard.py`)
* **개선 배경**: Python의 로컬 바이트 데이터 변수(`data`)가 클립보드 전송 완료 시점 전에 가비지 컬렉터에 의해 지워지면, C++ 레이어의 QImage가 참조하던 메모리가 손상되어 붙여넣기 오류나 비정상 종료가 발생할 수 있습니다.
* **구현**: QImage 생성 시 즉시 내부 버퍼를 복제 및 메모리 소유권을 Qt로 이관하는 `.copy()`를 추가하여 가비지 컬렉션 이슈를 원천 차단했습니다.
  ```python
  qim = QImage(data, image.size[0], image.size[1], QImage.Format_RGBA8888).copy()
  ```

### 4.3 트레이 아이콘 브랜드 로고 적용 (`ui/tray.py`)
* **개선 배경**: 기존 트레이 메뉴 실행 시 윈도우 시스템 기본 모니터 아이콘이 나타나 이질감이 있었습니다.
* **구현**: 프로젝트 루트에 위치한 `icon.ico`를 트레이 아이콘 이미지로 자동 불러오도록 수정하여 브랜드 아이덴티티를 통일시켰습니다.

---

## 5. 최종 결과 요약 (빌드 시간 정보)
* **DannyCapture_Single.exe**: 수정 완료 및 배포 폴더 업데이트 성공 (`2026-06-09` 22:25 기준 반영)
* **DannyCapture_Setup.exe**: 새 실행 파일을 포함하여 패키지 리빌드 완료.
* **테스트 결과**: 캡처 즉시 및 편집기 내 복사본을 붙여넣었을 때 **원본의 파란 형광색이 그대로 클립보드와 저장 파일에 반영됨을 확인**.

---

## 6. 향후 추가 작업 제안 (Next Steps)

1. **자동 업데이트 알림 구현**
   * `DannyCapture_Setup.exe`를 재배포할 때, 기존 설치되어 있는 구버전 클라이언트를 감지하여 자동으로 종료시키고 새 버전으로 덮어쓰는 설치 스크립트 고도화.
2. **트레이 메뉴 및 툴바 UI 한국어 통일**
   * 일부 팝업창 및 메뉴명의 영문 표기를 한글("Danny Capture Editor" ↔ "대니 캡처 편집기")로 매끄럽게 로컬라이징.
3. **단축키 중복 등록 예외 처리**
   * 윈도우 OS의 다른 프로그램(예: 캡처 도구, 메신저 등)과 단축키가 겹칠 경우 조용히 동작을 멈추는 대신, 사용자 알림 창을 띄워 환경설정으로 안내하는 예외 처리 추가.
4. **저장 기본 파일명 패턴 설정 기능**
   * 현재 "활성 창 제목 + 년월일 + 시분초"로 고정된 파일명 규칙을 사용자가 설정창에서 자유롭게 바꿀 수 있도록 옵션 제공.

---

# Danny Capture - 구현 및 수정 프로세스 기록 (2026-08-24)

본 세션은 「실행파일이 작동하지 않는다」는 신고에서 출발하여, 상태 진단 → 기능 수정 3건 → 개선 5건 구현 → 독립 리뷰로 결함 8건 추가 수정까지 진행한 기록입니다. 모든 변경은 소스에만 반영되어 있으며 **exe·설치본 재빌드는 미수행** 상태입니다(TODO 참조).

---

## 1. 실행 불가 신고 진단 (수정 없이 상태 확인)

* **오류현상**: 시작메뉴·바탕화면 아이콘으로 프로그램이 실행되지 않음.
* **오류원인분석**: 소스(13개 모듈 전부 임포트 통과)와 빌드 산출물(`dist/*.exe` 실행 확인, `Output/DannyCapture_Setup.exe` 존재)은 모두 정상. 실제 원인은 **설치 폴더(`%LOCALAPPDATA%/DannyCapture`)가 통째로 삭제**되어 바로가기만 깨진 링크로 남은 것. 제거 프로그램 레지스트리 항목도 부재.
* **해결및개선방법**: 사용자가 `DannyCapture_Setup.exe` 재실행으로 재설치하여 복구. 부수 발견 — `DannyCapture.spec`·`build.bat`·`main.py` 세 곳이 존재하지 않는 `app.ico` 를 참조(프로젝트에는 `icon.ico` 만 존재)하여 해당 빌드 경로가 깨져 있음(재빌드 시 정리 예정).

---

## 2. 사용자 요청 기능 수정 3건

### 2.1 색상 선택 창 자동 닫힘 (`ui/editor.py`)
* 편집기 `◑ 색상` 다이얼로그(QColorDialog, NoButtons)에서 색을 고른 뒤 창이 계속 떠 있는 불편 개선.
* `currentColorChanged` 직후 닫으면 그라데이션 드래그 중 눌리는 순간 닫혀버리므로, **색이 바뀐 뒤 마우스를 뗀 시점**에 닫도록 앱 전역 eventFilter + `MouseButtonRelease` 로 구현. 색상표 한 번 클릭 → 즉시 닫힘, 드래그 → 손을 뗄 때 확정.

### 2.2 기본 펜 색상 변경
* `DrawingScene.pen_color` 기본값 `#00B4F0`(하늘색) → `#FF0000`(빨강).

### 2.3 순간 팝업(드롭다운 등) 캡처 — 화면 동결 방식 도입
* **오류현상**: Chrome 주소창 자동완성 드롭다운을 띄운 채 캡처하면 결과물에 드롭다운이 없음.
* **오류원인분석**: 기존 흐름은 사용자가 드래그를 마치고 **마우스를 뗀 시점**에 `mss` 로 화면을 새로 촬영. 오버레이 위에서 클릭하는 순간 Chrome 이 포커스를 잃어 드롭다운이 닫히므로, 이미 사라진 뒤의 화면이 찍힘.
* **해결및개선방법**: Win+Shift+S 와 동일하게 **오버레이 표시 직전에 전체 가상 화면을 1회 동결**(`core/capture.py` 에 `freeze_screen()`/`crop_frozen()` 신설)하고, 선택 영역은 그 정지 화면에서 잘라내도록 변경(`ui/overlay.py` 생성자에서 동결, `ui/main_toolbar.py` `_on_region_captured` 가 `crop_frozen` 사용). 간편/전체/창/크기 4개 모드가 모두 이 경로를 공유.
* 검증: 파랑 창 동결 → 초록으로 변경 시나리오에서 동결본 크롭 = 파랑(구방식 라이브 촬영 = 초록으로 버그 재현) 확인.

---

## 3. 「수정했는데도 안 된다」 재신고 — 진단으로 밝혀진 원인 3건

기능 자체의 결함이 아니라 **검증 환경의 문제**가 겹쳐 있었음. 3시점 화면 저장 진단 스크립트로 실측하여 규명.

### 3.1 앱 인스턴스 중복 실행 (단축키 경합)
* **오류현상**: 캡처가 될 때와 안 될 때가 들쭉날쭉함.
* **오류원인분석**: `python` 실행이 껍데기 프로세스를 경유해, 종료했다고 판단한 PID 가 껍데기였고 실제 앱은 잔존. 한때 구버전 exe 2개 + `main.py` 2개가 동시에 떠 **같은 전역 단축키를 경합**(`RegisterHotKey` 는 선착 1개만 성공, 실패는 무통보).
* **해결및개선방법**: 명령줄 기준(`CommandLine LIKE '%main.py%'`)으로 전수 종료 후 단일 인스턴스만 유지. 근본 대책으로 §4.2 단일 인스턴스 뮤텍스 구현.

### 3.2 편집기 창이 뜨지 않음 — 실행 방식이 원인
* **오류현상**: 오버레이·드래그·파일 저장까지 정상인데 편집기 창만 나타나지 않음. 창 열거 결과 "Danny Capture Editor" 창이 **존재하되 Visible=False**.
* **오류원인분석**: 에이전트가 앱을 `-WindowStyle Hidden` 으로 기동한 탓. Windows 는 STARTUPINFO 의 SW_HIDE 를 **그 프로세스의 첫 최상위 창**에 강제 적용하는데, 이 앱은 툴바를 숨긴 채 시작하므로 편집기가 첫 창이 되어 `show()` 가 무시됨. 통제 실험으로 확정(Hidden 실행 visible=False / 일반 실행 visible=True).
* **해결및개선방법**: `pythonw.exe` 로 숨김 플래그 없이 기동하도록 실행 절차 변경. 프로그램 코드 결함 아님 — exe 직접 실행 시에는 발생하지 않는 문제.

### 3.3 캡처 중 드롭다운이 화면에서 사라져 보임 (`ui/overlay.py`)
* **오류현상**: 결과물에는 드롭다운이 담기지만, 선택하는 동안 화면에서는 사라져 보여 무엇을 선택하는지 알 수 없음.
* **오류원인분석**: 오버레이가 반투명(WA_TranslucentBackground)이라 그 아래 **라이브 화면**이 비침. 클릭 순간 실제 드롭다운이 닫히면 화면 표시도 함께 사라짐(캡처 데이터는 동결본이라 무사).
* **해결및개선방법**: **동결 스크린샷을 오버레이 배경으로 직접 그리도록** 변경. 동결본 하나가 배경·돋보기·최종 크롭에 모두 쓰여 「화면에 보이는 것 = 돋보기 = 저장되는 것」이 픽셀 단위로 일치. 선택 영역은 투명 뚫기 대신 동결본을 원래 밝기로 재노출. 실측 3항목(표시 중 어두운 동결색 유지 / 선택 영역 원본 밝기 / 최종 크롭 일치) 통과.

---

## 4. 개선 5건 구현 (다중 에이전트 코드 리뷰로 후보 발굴 → 사용자 선정)

4개 관점(기능 공백·견고성·UX·설정 불일치) 병렬 리뷰로 후보 목록을 만들고, 사용자가 0순위 3건 + Crop + 재캡처를 선정.

### 4.1 저장 경로 하드코딩 제거 (`utils/config.py`)
* **오류현상(잠재)**: 설정창에서 저장 폴더를 바꿔도 재시작하면 원복. 타 PC 설치 시 존재하지 않는 개발자 경로에 저장 시도.
* **오류원인분석**: `load()` 가 매 실행마다 `C:/Users/cho/.../03 Capture` 를 강제 대입 후 저장까지 수행.
* **해결및개선방법**: 강제 대입 제거, 기본값을 `Path.home()/Pictures/DannyCapture` 로 이식 가능하게 변경. 기존 사용자 config 의 `03 Capture` 경로는 그대로 유지됨(병합 로드). 죽은 설정 `ask_save`·미구현 `scroll_capture` 키 제거, `auto_save` 기본 True + 사용자 config 이관으로 기존 동작 보존.

### 4.2 단일 인스턴스 + 단축키 등록 실패 알림 (`main.py`, `core/hotkey_manager.py`)
* 명명 뮤텍스(`DannyCapture_SingleInstance`)로 중복 실행 시 안내 후 종료. §3.1 재발 방지.
* `RegisterHotKey` 실패를 `failed_hotkeys` 로 수집, 시작 시 트레이 경고 + 설정 저장 시 경고창. 기존 코드는 실패해도 무조건 "성공" 을 출력했음.

### 4.3 저장 흐름 정리 (`ui/main_toolbar.py`, `ui/editor.py`, `ui/settings_dialog.py`)
* `auto_save` 설정이 실제로 동작(설정창에 체크박스 노출). 저장 try/except — 실패 시 알림을 띄우되 **편집기는 유지해 캡처를 잃지 않음**.
* 편집기 저장 기본 경로 = 자동 저장된 그 파일(`source_filepath` 전달) → **이중 파일 생성 제거**. `QImage.save()` 반환값 검증 — 실패를 "저장 완료" 로 오보하던 문제 수정.

### 4.4 ✂ 자르기 도구 (`ui/editor.py`)
* crop 모드: 점선 사각형 드래그 → 장면 전체(주석 포함)를 QImage 로 베이크 후 크롭, undo 스택 리셋. 5px 미만 선택 무시, 화면 밖 클램프.

### 4.5 마지막 영역 재캡처 (`Ctrl+Alt+R`)
* 영역 캡처 시 `last_region` 을 config 에 기록(재시작 후에도 유지) → 단축키 한 번으로 오버레이 없이 즉시 재캡처. 트레이 메뉴·설정창 단축키 항목 추가. 영역 미기록 시 안내 알림.

---

## 5. 독립 검증(Worker–Evaluator)과 결함 8건 추가 수정

작성 과정을 모르는 검증 에이전트 3팀(회귀/신규 로직/수명주기)에게 변경 내역만 주고 적대적 리뷰 수행. 3팀이 독립적으로 동일 결함에 수렴(major 4·minor 다수, 중복 제거 후 8건). 전부 수정.

* **연속 캡처 시 이전 편집기 GC 파괴** — `self.editor` 재대입으로 편집 중 창이 소리 없이 소멸, 주석 소실. → 편집기 목록 보관 + `WA_DeleteOnClose` + destroyed 시 목록 제거. 여러 캡처 동시 편집 가능해짐.
* **자동 저장 실패 시 편집기 저장 버튼도 같은 원인으로 사망** — 구제 경로의 `get_new_filepath()` 가 동일 무효 경로에서 OSError. → try/except + `Pictures` 폴백.
* **단축키 오타가 잘못된 전역 조합을 등록** — 파서가 모르는 토큰을 조용히 버려 `ctrl+ait+r` 이 전역 Ctrl+R 로 등록됨. → 미인식 토큰 = 무효 조합으로 판정해 실패 목록에 보고.
* **동일 단축키 2개 기능 설정 시 한 기능이 무통보 증발** — dict 키 충돌. → 리스트 순회 + (mod,vk) 중복 감지, "…와 중복" 사유로 보고.
* **모니터 구성 변경 후 재캡처가 검은 이미지를 "완료" 로 저장** — mss 가 화면 밖 좌표에도 예외 없이 검은 픽셀 반환. → 현재 가상 화면과 교차 검증, 화면 밖이면 안내 후 중단.
* **뮤텍스 판정 GetLastError 신뢰성** — ctypes 내부 동작이 last-error 를 덮을 수 있음(공식 문서 명시). → `WinDLL(use_last_error=True)` + `ctypes.get_last_error()`.
* **자르기 버튼 재클릭 시 체크만 풀리고 crop 모드 잔존** — 의도치 않은 파괴적 크롭. → 활성 도구 재클릭 시 체크 유지.
* **설정 변경 후 트레이 메뉴 라벨 미갱신**(기존부터 있던 문제) — `refresh_labels()` 신설, 설정 저장 시 호출.

---

## 6. 검증 결과

* 자동 테스트 하네스 `scratch/test_improvements.py` — 임시 APPDATA 격리, **37/37 PASS** (경로 이식성·뮤텍스·단축키 실패/중복/오타 감지·저장 3경로·크롭 경계·재캡처·리뷰 수정 8건 회귀).
* `scratch/test_overlay_freeze.py` — 동결 배경 표시 실측 **3/3 PASS**.
* 실기기 확인: 사용자가 드롭다운 캡처·자동 닫힘·기본색·자르기·재캡처 정상 동작 확인.
* 흥미로운 부수 실증: 앱 실행 중 하네스를 돌리면 뮤텍스·단축키 6종 선점이 그대로 감지됨(3건 FAIL) — 프로세스 간 차단이 실제로 동작한다는 증거. 앱 종료 후 재실행 시 37/37.
* [HUMAN CHECK] 다중 모니터 배율 125%/150% 환경 미검증 — 본 세션의 모니터 3대는 전부 100%(dpr=1.0)였음. 재캡처의 「모니터 분리」 시나리오는 좌표 시뮬레이션으로만 검증.

---

## 7. 작업 중 발생한 도구 오류 (재발 방지 기록)

* **bash heredoc 백슬래시 소실**: `python - <<'PY'` 안의 `r"C:\Users\..."` 가 전달 중 `\U` 로 깨져 SyntaxError. → 패치 스크립트를 파일로 저장 후 실행하는 방식으로 전환.
* **후행 공백 앵커 불일치**: 원본 소스의 빈 줄들에 후행 공백이 있어 exact-match 패치가 반복 실패. → 라인별 `[ \t]*` 허용 fuzzy 매칭으로 전환.
* **re.sub 치환문자열의 `\n` 이스케이프 해석**: 치환문에 넣은 리터럴 `\n` 이 실제 개행으로 풀려 `settings_dialog.py` 문자열이 파손·컴파일 실패. → 라인 단위 수술로 복구. re.sub 치환문에는 백슬래시 시퀀스를 두지 않는다.

---

## 8. 향후 TODO (다음 세션)

1. **exe·설치본 재빌드** — 오늘 변경 전부가 소스에만 있음. `DannyCapture_Single.spec` 로 빌드 후 `installer.iss` 재패키징. 이때 `DannyCapture.spec`·`build.bat`·`main.py` 의 깨진 `app.ico` 참조를 `icon.ico` 로 정리.
2. **installer.iss 에 실행 중 구버전 종료 처리** — 이제 앱에 뮤텍스가 생겼으므로 `AppMutex=DannyCapture_SingleInstance` 지시자 활용 가능.
3. 미착수 개선 후보(우선순위 순): 모자이크/블러(민감정보 가리기) · 캡처 이미지 화면 핀 고정 · OCR 텍스트 추출 · 트레이 「저장 폴더 열기」 · 편집기 fit-to-window.
4. spec 의 `datas=[]` 라 `icon.ico` 가 exe 에 미내장 → onefile 실행 시 트레이 아이콘 폴백 문제(리뷰 지적, 미수정) — 재빌드 시 함께 처리.

---

## 9. Git 공유 및 v1.2.0 배포 (2026-08-24 야간 — 같은 날 추가 세션)

「다른 사람과 공유하고 싶다. 지난번 zip 으로 받아 설치하려다 문제가 있었다」는 요청으로, 배포 체계를 GitHub 저장소 + Releases 구조로 구축.

### 9.1 zip 공유가 실패했던 원인 진단
* 소스 zip 은 실행 파일이 아니므로 받는 쪽에 Python + 의존 패키지 설치가 필요했음.
* 설령 소스로 실행했더라도 §4.1 의 저장 경로 하드코딩(금일 오전 수정) 때문에 타 PC 에서는 저장이 실패하는 상태였음.
* 결론: 소스는 git 으로, 일반 사용자는 GitHub Releases 의 `DannyCapture_Setup.exe` 로 받는 구조가 정답.

### 9.2 빌드 전 정비 (§8 TODO 1·2·4 해소)
* `requirements.txt` 정리 — 전 모듈 임포트 전수 조사로 `rembg`(대용량)·`pynput`(네이티브 단축키 전환으로 폐기) **미사용 확정 후 제거.** 잔여: PySide6·mss·Pillow·winotify·pywin32.
* 깨진 `app.ico` 참조 3곳(`main.py`·`DannyCapture.spec`·`build.bat`) → `icon.ico` 로 정정.
* 두 spec 의 `datas` 에 `icon.ico` 내장 → onefile 실행 시 트레이 아이콘 폴백 문제 해소(§5 리뷰 지적 잔여분).
* `installer.iss` 에 `AppMutex=DannyCapture_SingleInstance` 추가 — 금일 구현한 뮤텍스와 연동되어, 설치 시 실행 중인 구버전을 감지·종료 안내.

### 9.3 재빌드 및 스모크 테스트
* `DannyCapture_Single.exe` 재빌드(PyInstaller 6.16, 68.4MB) — 금일 수정 전량 포함. 첫 배포 이후 처음으로 소스와 exe 가 일치하는 상태가 됨.
* `DannyCapture_Setup.exe` 재패키징(Inno Setup 6, 70.4MB).
* 스모크 테스트: 새 exe 실행 유지 확인. **뮤텍스 교차검증** — 2번째 인스턴스 실행 시 안내창을 띄우며 차단됨(프로세스 간 실증).

### 9.4 Git 저장소 구축 및 배포

* **오류현상**: 최초 `git add -A` 스테이징 목록에 `installer/DannyCapture_Setup.exe`(4월자 구버전 68MB 바이너리)와 `scratch/*.err` 로그가 포함됨.
* **오류원인분석**: `.gitignore` 를 이름 규칙(`Output/`·`dist/`) 중심으로 짜서 **폴더 단위 보관물**(`installer/`)이 그물 밖이었음 — CLAUDE.md 2항이 경고한 「폴더 단위 산출물 누락」과 동일 유형.
* **해결및개선방법**: `installer/`·`scratch/*.err` 규칙 추가 후 `git rm --cached` 로 스테이징 해제. `git check-ignore` 로 대상 5종(dist·Output·build·.initial_setting·diag_shots) 차단 실측 확인. **커밋 전 스테이징 목록을 눈으로 전수 확인하는 절차가 유효했음** — status 만 믿었다면 68MB 바이너리가 저장소에 들어갔음.

* `.gitignore` 에 CLAUDE.md 필수 4종(`.env*`·`.agent/`·`*.pem`·`*credentials*.json`) 포함.
* **시크릿 게이트 4종 전부 PASS** (패턴 grep 0건 · 스테이징 추가 라인 0건 · .env 추적 없음 · .env 이력 없음). `nginx_patch.conf` 는 내용 점검 결과 일반 프록시 설정만 있어 포함 유지.
* 커밋 `bf08a44` (34개 파일: 소스·spec·installer.iss·문서·테스트 하네스) → GitHub **public 저장소 `bignine99/danny-capture`** 생성·푸시.
* **Release v1.2.0** 생성, `DannyCapture_Setup.exe`(70,389,496 bytes) 자산 첨부를 API 로 재확인.
* `README_KR.md` 전면 갱신 — 일반 사용자용 설치 절차(Releases 링크), zip 방식 경고, v1.2.0 변경 이력, 개발자용 빌드 절차.
* 공유 링크: `https://github.com/bignine99/danny-capture/releases/latest`

### 9.5 /99 재검증
* 배포 직후 /99 호출로 게이트 4종 재실행 — 전부 통과, 추가 커밋할 변경 0건(로컬 = 원격 `bf08a44`).

---

## 10. TODO 상태 갱신 (§8 대비)

| §8 항목 | 상태 |
|---|---|
| 1. exe·설치본 재빌드 + app.ico 정리 | **완료** (§9.2~9.3) |
| 2. installer.iss 구버전 종료 처리(AppMutex) | **완료** (§9.2) |
| 3. 미착수 개선 후보(모자이크/블러·핀 고정·OCR·트레이 폴더 열기·fit-to-window) | 잔여 |
| 4. icon.ico exe 내장 | **완료** (§9.2) |

### 신규 TODO
1. ~~타 PC 설치 테스트~~ — **완료(2026-08-24)**: 사용자가 타 PC 에서 설치 정상·저장 폴더 정상을 직접 확인. v1.2.0 배포 검증 종료.
2. 이후 버전 배포 절차(확립): 소스 수정 → `python -m PyInstaller --clean DannyCapture_Single.spec` → `ISCC.exe installer.iss` → `gh release create v1.x.x Output/DannyCapture_Setup.exe` (링크는 `releases/latest` 불변).
3. §8-3 잔여 개선 후보는 우선순위 재논의 후 착수.
