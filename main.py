import flet as ft
import yt_dlp
import sys, os, platform, re, subprocess
 
#pyInstaller打包后生成的可执行文件可能在一个较小的环境中运行，缺少一些环境变量，特别是 PATH
sys_dir = ['/bin', '/sbin', '/usr/bin', '/usr/sbin', '/usr/local/bin', '/usr/local/sbin']
os.environ['PATH'] += os.pathsep.join(sys_dir)
 
dir = os.path.join(os.path.expanduser("~"), "Desktop")
findcmd = "whereis"
 
if "Windows" in platform.system():
    findcmd = "where"
 
ansi_escape_pattern = re.compile(r'\x1B\[[0-?9;]*[mK]')
# 定义视频和音频格式
video_format = 'bestvideo[ext=mp4]+bestaudio[ext=m5a]/mp4'
audio_format = 'bestaudio[ext=m4a]'
# 创建 yt-dlp 的选项
ydl_opts = {
    'format': f'{video_format}/{audio_format}',
    'outtmpl':f'{dir}/%(title)s.%(ext)s',
    'ffmpeg_location' : None, 
}
 
try:
    # 使用which命令查output找ffmpeg
    result = subprocess.run([findcmd, 'ffmpeg'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    output = result.stdout.decode().strip()
    # 解析输出以获取绝对路径
    if "Windows" in platform.system():
        ffmpeg_paths = output.strip().split()
    else:
        ffmpeg_paths = output.split(':')[-1].strip().split()
 
    if ffmpeg_paths:
        # 取第一个路径
        ffmpeg_path = ffmpeg_paths[0].strip()
        real_ffmpeg_path = os.path.realpath(ffmpeg_path).strip()
        ydl_opts['ffmpeg_location'] = real_ffmpeg_path
except Exception as e:
    pass
 
 
def main(page: ft.Page):
    page.appbar = ft.AppBar(
        title=ft.Text("Youtube Video Downloader"),
        center_title=True
    )
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
 
    def textChanged(e):
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                URL = e.control.value
                video = ydl.extract_info(URL, download=False)
                button.text = "下载: " + video.get("title")
                button.disabled = False
                image.src = video.get("thumbnail")
                image.update()
        except Exception as e:
            button.text = "下载视频"
            button.disabled = True
            snackbar = ft.SnackBar(
                ft.Text("这不是一个合法的youtube链接!",
                    color=ft.colors.RED_500,
                    )
                )
            snackbar.open = True  # 设置 SnackBar 为打开状态
            page.overlay.append(snackbar)  # 将 SnackBar 添加到 overlay
            page.update()  # 更新页面
        button.update()
 
    def on_progress(stream):
        percent = ansi_escape_pattern.sub('', stream.get("_percent_str"))
        if stream.get("status") == 'finished':
            button.text = f"完成了 ... {percent}"
            button.disabled = False
        else:
            button.text = f"下载中 ... {percent}"
            button.disabled = True
        button.update()
 
    def download(e):
        ydl_opts['progress_hooks'] = [on_progress]
        if radio_fmt.value == "audio":
            ydl_opts['format'] = f'{audio_format}'
        else:
            ydl_opts['format'] = f'{video_format}/{audio_format}'
 
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download(url_input.value)
        except Exception as e:
            with open("/var/tmp/error.log", "a+") as f:
                f.write(f"{e} \n")
 
    url_input = ft.TextField(
        hint_text="请提交youtube链接：",
        min_lines=1,
        autofocus=True,
        on_change=textChanged,
    )
    image = ft.Image(
        src="https://play-lh.googleusercontent.com/LW4J1mC4nLnoQpRu37Od-fMzgHbOE2A1VyGQBnpMG4xZosP6c1iPtXFyHmPq_H2QcRCh=w480-h960-rw",
        width = 225,
        fit = ft.ImageFit.COVER
        )
    button = ft.ElevatedButton(
        "下载音视频资源!",
        disabled=True,
        on_click=download,
    )
    radio_fmt = ft.RadioGroup(
            content=ft.Row([
                ft.Radio(label="视频", value="video"),
                ft.Radio(label="音频", value="audio"),
            ]),
            value="video",  # 默认值设置为视频
            on_change=lambda e: update_button(e.control.value),
    )
    dir_text =  ft.Text(f"保存: {dir}")
    if ydl_opts.get("ffmpeg_location") == None:
        radio_fmt.value = "audio"
 
    # 更新按钮文本的函数
    def update_button(selected_value):
        if ydl_opts.get("ffmpeg_location") == None:
            radio_fmt.value = "audio"
            button.text = f"视频必须安装【ffmpeg】,音频正常下载！"
        else:
            selected_str = "音频" if selected_value == "audio" else "视频"
            button.text = f"下载: {selected_str}"
        radio_fmt.update()
        button.update()
 
    page.add(
        image,
        url_input,
        radio_fmt,
        button,
        dir_text
    )
 
    page.update()
 
ft.app(target=main)