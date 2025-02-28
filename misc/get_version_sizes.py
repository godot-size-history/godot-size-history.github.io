import io
import sys
import zipfile

import requests


def get_download_size(url: str) -> int:
    response = requests.head(url, allow_redirects=True)
    if response.status_code == 200 and "Content-Length" in response.headers:
        return int(response.headers["Content-Length"])
    return -1


def get_export_template_sizes(url: str) -> dict[str, tuple[str, str]]:
    export_download_size = get_download_size(url)
    export_compressed_size = f"{export_download_size / (1e6):.3f}"

    sizes: dict[str, tuple[str, str]] = {}

    linux_template_name = (
        "templates/linux_release.x86_64"
        if version[0] == '4'
        else "templates/linux_x11_64_release"
    )
    windows_template_name = (
        "templates/windows_release_x86_64.exe"
        if version[0] == '4'
        else "templates/windows_64_release.exe"
    )
    web_template_name = (
        "templates/web_release.zip"
        if version[0] == '4'
        else "templates/webassembly_release.zip"
    )

    response = requests.get(url)
    if response.status_code == 200:
        with zipfile.ZipFile(io.BytesIO(response.content)) as z:
            template_extracted_size: int = 0
            for info in z.infolist():
                template_extracted_size += info.file_size
                if info.filename == linux_template_name:
                    compressed_size = f"{info.compress_size / (1e6):.3f}"
                    uncompressed_size = f"{info.file_size / (1e6):.3f}"
                    sizes["export_linux"] = (compressed_size, uncompressed_size)
                elif info.filename == windows_template_name:
                    compressed_size = f"{info.compress_size / (1e6):.3f}"
                    uncompressed_size = f"{info.file_size / (1e6):.3f}"
                    sizes["export_windows"] = (compressed_size, uncompressed_size)
                elif info.filename == web_template_name:
                    compressed_size = f"{info.file_size / (1e6):.3f}"
                    with zipfile.ZipFile(io.BytesIO(z.read(info.filename))) as z2:
                        uncompressed_size = f"{(sum(info.file_size for info in z2.infolist())) / (1e6):.3f}"
                        sizes["export_web"] = (compressed_size, uncompressed_size)
            sizes["export_all"] = (
                export_compressed_size,
                f"{template_extracted_size / (1e6):.3f}",
            )

    return sizes


def get_extracted_size_editor(url: str, version: str, linux: bool) -> int:
    response = requests.get(url)
    if response.status_code != 200:
        return -1
    target = f"Godot_v{version}_win64.exe"
    if linux:
        if version[0] == '4':
            target = f"Godot_v{version}_linux.x86_64"
        else:
            target = f"Godot_v{version}_x11.64"
    with zipfile.ZipFile(io.BytesIO(response.content)) as z:
        for info in z.infolist():
            if info.filename == target:
                return info.file_size
    return -1


def get_version_sizes(version: str) -> dict[str, tuple[str, str]]:
    base_url = f"https://github.com/godotengine/godot/releases/download/{version}/Godot_v{version}"
    editor_url_linux = (
        f"{base_url}_linux.x86_64.zip"
        if version[0] == '4'
        else f"{base_url}_x11.64.zip"
    )
    editor_url_windows = f"{base_url}_win64.exe.zip"
    export_templates_url = f"{base_url}_export_templates.tpz"

    sizes: dict[str, tuple[str, str]] = {}

    editor_download_size_linux = get_download_size(editor_url_linux)
    editor_compressed_size_linux = f"{editor_download_size_linux / (1e6):.3f}"
    editor_extracted_size = get_extracted_size_editor(editor_url_linux, version, True)
    editor_extracted_size_linux = f"{editor_extracted_size / (1e6):.3f}"
    sizes["editor_linux"] = (editor_compressed_size_linux, editor_extracted_size_linux)

    editor_download_size_windows = get_download_size(editor_url_windows)
    editor_compressed_size_windows = f"{editor_download_size_windows / (1e6):.3f}"
    editor_extracted_size = get_extracted_size_editor(
        editor_url_windows, version, False
    )
    editor_extracted_size_windows = f"{editor_extracted_size / (1e6):.3f}"
    sizes["editor_windows"] = (
        editor_compressed_size_windows,
        editor_extracted_size_windows,
    )

    export_extracted_size = get_export_template_sizes(export_templates_url)
    sizes |= export_extracted_size

    return sizes


def sizes_to_str(sizes: tuple[str, str]) -> str:
    # size_list = [num.rstrip("0").rstrip(".") for num in sizes]
    # return f"{size_list[0]} / {size_list[1]}"
    return f"{sizes[0]} / {sizes[1]}"


def main(version: str) -> None:
    sizes = get_version_sizes(version)
    print(f"Godot version: {version}")
    print("  file | download / extracted")
    if windows_sizes := sizes.get("editor_windows"):
        print(f"  - Windows: {sizes_to_str(windows_sizes)}")
    if linux_sizes := sizes.get("editor_linux"):
        print(f"  - Linux: {sizes_to_str(linux_sizes)}")
    if export_windows_sizes := sizes.get("export_windows"):
        print(f"  - Export templates Windows: {sizes_to_str(export_windows_sizes)}")
    if export_linux_sizes := sizes.get("export_linux"):
        print(f"  - Export templates Linux: {sizes_to_str(export_linux_sizes)}")
    if export_web_sizes := sizes.get("export_web"):
        print(f"  - Export templates HTML5: {sizes_to_str(export_web_sizes)}")
    if export_all_sizes := sizes.get("export_all"):
        print(f"  - Export templates - all: {sizes_to_str(export_all_sizes)}")


if __name__ == "__main__":
    version = sys.argv[1]
    main(version)
