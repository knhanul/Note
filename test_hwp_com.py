#!/usr/bin/env python3
"""
Standalone test script for Hancom HWP COM automation.
Run this script independently to test if Hancom COM is working correctly.
"""

import sys
import subprocess
from pathlib import Path


def check_hwp_running():
    """Check if Hancom HWP is running in the system."""
    try:
        # Check for HWP-related processes
        result = subprocess.run(
            ["tasklist"], 
            capture_output=True, 
            text=True, 
            shell=True
        )
        output = result.stdout.lower()
        hwp_processes = [line for line in output.split('\n') if 'hwp' in line or 'hancom' in line]
        return hwp_processes
    except Exception:
        return []


def test_hwp_com():
    """Test Hancom HWP COM automation with detailed error reporting."""
    print("=" * 60)
    print("한글 COM 자동화 테스트")
    print("=" * 60)
    print()

    # Check if HWP is running
    print("시스템 프로세스 확인:")
    print("-" * 60)
    hwp_processes = check_hwp_running()
    if hwp_processes:
        print("한글 관련 프로세스가 실행 중입니다:")
        for proc in hwp_processes:
            print(f"  - {proc}")
    else:
        print("한글 관련 프로세스가 실행 중이 아닙니다.")
        print("  한글을 먼저 실행한 후 다시 시도해 보세요.")
    print()

    # Check pywin32 installation
    try:
        import pythoncom
        import win32com.client
        print("✓ pywin32가 설치되어 있습니다.")
    except ImportError as exc:
        print(f"✗ pywin32가 설치되어 있지 않습니다: {exc}")
        print("  설치 명령: pip install pywin32")
        return False

    # Check Python bitness
    import platform
    python_bits = platform.architecture()[0]
    print(f"Python 비트 수: {python_bits}")
    if python_bits == "64bit":
        print("  주의: 한글이 32비트인 경우 COM 연결이 실패할 수 있습니다.")
    print()

    # Test different ProgIDs and dispatch methods
    # Hancom 2024 might use different ProgIDs
    prog_ids = [
        "HWPFrame.HwpObject",  # Traditional
        "Hwp.HwpObject",        # Alternative
        "Hwp.Application",      # Application-level
        "Hancom.HwpObject",     # Hancom-specific
        "HWP.HwpObject.1",      # Versioned
    ]
    # Try Dispatch first (connects to running instance), then DispatchEx
    methods = [("Dispatch", win32com.client.Dispatch), ("DispatchEx", win32com.client.DispatchEx)]

    hwp = None
    successful_prog_id = None
    successful_method = None
    errors = []

    print("\nCOM 객체 생성 시도:")
    print("-" * 60)

    for prog_id in prog_ids:
        for method_name, dispatch in methods:
            try:
                print(f"  시도: {method_name}('{prog_id}')...", end=" ")
                pythoncom.CoInitialize()
                hwp = dispatch(prog_id)
                pythoncom.CoUninitialize()
                print("✓ 성공")
                successful_prog_id = prog_id
                successful_method = method_name
                break
            except Exception as exc:
                error_msg = f"{method_name}('{prog_id}'): {exc}"
                print(f"✗ 실패 - {exc}")
                errors.append(error_msg)
            finally:
                # Clean up if we got an object but it's not the final one
                if hwp is not None and successful_prog_id is None:
                    try:
                        hwp.Quit()
                    except Exception:
                        pass
                    hwp = None
        if successful_prog_id:
            break

    if hwp is None:
        print("\n" + "=" * 60)
        print("결과: COM 객체 생성 실패")
        print("=" * 60)
        print("\n시도한 ProgID:")
        for prog_id in prog_ids:
            print(f"  - {prog_id}")
        print("\n상세 에러:")
        for error in errors:
            print(f"  - {error}")
        print("\n가능한 원인:")
        print("  1. 한글이 설치되어 있지 않거나 COM 등록이 되지 않음")
        print("  2. Python과 한글의 비트 수가 다름 (32비트/64비트 불일치)")
        print("  3. 한글이 제대로 설치되지 않음")
        print("\n해결 방법:")
        print("  - 한글이 설치되어 있는지 확인")
        print("  - Python과 한글의 비트 수가 일치하는지 확인")
        print("  - 관리자 권한으로 한글을 재설치")
        return False

    print("\n" + "=" * 60)
    print("결과: COM 객체 생성 성공")
    print("=" * 60)
    print(f"ProgID: {successful_prog_id}")
    print(f"Method: {successful_method}")
    print()

    # Test basic operations
    print("\n객체 정보 확인:")
    print("-" * 60)
    print(f"객체 타입: {type(hwp)}")
    print(f"객체 클래스: {hwp.__class__}")
    print(f"객체 repr: {repr(hwp)}")

    # Check available attributes
    print("\n사용 가능한 속성/메서드:")
    try:
        attrs = [attr for attr in dir(hwp) if not attr.startswith('_')]
        if attrs:
            for attr in attrs[:20]:  # Show first 20
                print(f"  - {attr}")
            if len(attrs) > 20:
                print(f"  ... (총 {len(attrs)}개)")
        else:
            print("  (속성 없음)")
    except Exception as exc:
        print(f"  속성 확인 실패: {exc}")

    print("\n기본 작업 테스트:")
    print("-" * 60)

    try:
        pythoncom.CoInitialize()
        
        # Test visibility
        try:
            hwp.XHwpWindows.Item(0).Visible = False
            print("  ✓ Visible 설정 성공")
        except Exception as exc:
            print(f"  ✗ Visible 설정 실패: {exc}")

        # Test RegisterModule
        try:
            hwp.RegisterModule("FilePathCheckDLL", "FilePathCheckerModule")
            print("  ✓ RegisterModule 성공")
        except Exception as exc:
            print(f"  ✗ RegisterModule 실패: {exc}")

        # Test creating a new document
        try:
            hwp.NewDoc()
            print("  ✓ 새 문서 생성 성공")
        except Exception as exc:
            print(f"  ✗ 새 문서 생성 실패: {exc}")

        # Test SaveAs to HWPX
        test_hwpx = Path.cwd() / "test_com_output.hwpx"
        try:
            saved = bool(hwp.SaveAs(str(test_hwpx.resolve()), "HWPX", ""))
            if saved and test_hwpx.exists():
                print(f"  ✓ HWPX 저장 성공: {test_hwpx}")
                test_hwpx.unlink()  # Clean up
            else:
                print(f"  ✗ HWPX 저장 실패: 파일이 생성되지 않음")
        except Exception as exc:
            print(f"  ✗ HWPX 저장 실패: {exc}")

        # Quit
        try:
            hwp.Quit()
            print("  ✓ 한글 종료 성공")
        except Exception as exc:
            print(f"  ✗ 한글 종료 실패: {exc}")

        pythoncom.CoUninitialize()

    except Exception as exc:
        print(f"\n✗ 기본 작업 테스트 중 오류: {exc}")
        pythoncom.CoUninitialize()
        return False

    print("\n" + "=" * 60)
    print("테스트 완료")
    print("=" * 60)
    return True


if __name__ == "__main__":
    success = test_hwp_com()
    sys.exit(0 if success else 1)
