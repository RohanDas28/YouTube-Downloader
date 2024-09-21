import yt_dlp
from concurrent.futures import ThreadPoolExecutor, as_completed
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import os
import time

# Global variable to store download folder
download_folder = ""

# Function to get format based on user's selection
def get_format_choice(choice):
    if choice == '4k':
        return {
            'format': 'bestvideo[ext=mp4][height<=2160]+bestaudio[ext=m4a]/best[ext=mp4][height<=2160]',
            'merge_output_format': 'mp4'
        }
    else:
        return {
            'format': 'bestvideo[ext=mp4][height<=1080]+bestaudio[ext=m4a]/best[ext=mp4][height<=1080]',
            'merge_output_format': 'mp4'
        }

# Function to update GUI progress labels, progress bar, and download speed
def update_gui(video_num, total_videos, completed_videos, download_speed=None):
    progress_label.config(text=f"Video {video_num}/{total_videos}")
    downloaded_label.config(text=f"Downloaded: {completed_videos}")
    remaining_label.config(text=f"Remaining: {total_videos - completed_videos}")
    if download_speed:
        speed_label.config(text=f"Speed: {download_speed:.2f} KB/s")
    progress_bar['value'] = (completed_videos / total_videos) * 100
    root.update_idletasks()

# Function to download a video and update progress and download speed
def download_video(url, ydl_opts, video_num, total_videos, completed_videos):
    start_time = time.time()
    try:
        def progress_hook(d):
            if d['status'] == 'downloading':
                download_speed = d.get('speed', 0) / 1024  # Convert to KB/s
                update_gui(video_num, total_videos, completed_videos[0], download_speed)
        
        ydl_opts['progress_hooks'] = [progress_hook]
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        completed_videos[0] += 1  # Update count in shared list
        update_gui(video_num, total_videos, completed_videos[0])
    except Exception as e:
        print(f"An error occurred while downloading {url}: {e}")

# Function to download multiple videos in parallel
def download_videos_in_parallel(urls, ydl_opts, max_threads=4):
    completed_videos = [0]
    total_videos = len(urls)
    update_gui(0, total_videos, completed_videos[0])

    with ThreadPoolExecutor(max_workers=max_threads) as executor:
        future_to_url = {executor.submit(download_video, url, ydl_opts, i + 1, total_videos, completed_videos): url for i, url in enumerate(urls)}
        for future in as_completed(future_to_url):
            future.result()

# Function to download a playlist and update GUI
def download_playlist(playlist_url, ydl_opts, max_threads=4):
    try:
        ydl_opts['extract_flat'] = True  # Extract video URLs without downloading immediately

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(playlist_url, download=False)
            video_urls = [entry['url'] for entry in info_dict['entries']]

        # Download videos in parallel
        download_videos_in_parallel(video_urls, ydl_opts, max_threads)

        messagebox.showinfo("Success", "Playlist download complete!")
    except Exception as e:
        print(f"An error occurred while downloading playlist: {e}")
        messagebox.showerror("Error", f"An error occurred: {e}")

# Function to run the download in a separate thread
def run_download_thread(url, quality):
    try:
        ydl_opts = get_format_choice(quality)
        if download_folder:
            ydl_opts['outtmpl'] = os.path.join(download_folder, '%(title)s.%(ext)s')
        else:
            ydl_opts['outtmpl'] = '%(title)s.%(ext)s'
        
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegVideoConvertor',
            'preferedformat': 'mp4',
        }]

        if 'playlist' in url.lower():
            download_playlist(url, ydl_opts, max_threads=4)  # Adjust threads as needed
        else:
            download_video(url, ydl_opts, 1, 1, [0])
    finally:
        download_button.config(state=tk.NORMAL)  # Re-enable the button once the download is complete

# Function to start the download in a new thread
def start_download():
    url = url_entry.get().strip()
    quality = quality_choice.get()

    if not url:
        messagebox.showerror("Error", "Please enter a YouTube URL")
        return

    if not download_folder:
        messagebox.showerror("Error", "Please select a download folder")
        return

    # Disable the download button to prevent multiple clicks
    download_button.config(state=tk.DISABLED)

    # Start the download in a separate thread
    threading.Thread(target=run_download_thread, args=(url, quality), daemon=True).start()

# Function to select download folder
def select_download_folder():
    global download_folder
    folder = filedialog.askdirectory()
    if folder:
        download_folder = folder
        folder_label.config(text=f"Download Folder: {folder}")

# Function to handle GUI closing
def on_closing():
    if messagebox.askokcancel("Quit", "Do you want to quit?"):
        root.quit()
        root.destroy()

# Build GUI
root = tk.Tk()
root.title("YouTube Downloader")

# URL input
url_label = tk.Label(root, text="YouTube Video/Playlist URL:")
url_label.pack(pady=5)
url_entry = tk.Entry(root, width=50)
url_entry.pack(pady=5)

# Quality choice (4K or 1080p)
quality_choice = tk.StringVar(value='1080p')
quality_label = tk.Label(root, text="Select Quality:")
quality_label.pack(pady=5)
quality_4k = tk.Radiobutton(root, text="4K", variable=quality_choice, value='4k')
quality_4k.pack(anchor=tk.W, padx=20)
quality_1080p = tk.Radiobutton(root, text="1080p", variable=quality_choice, value='1080p')
quality_1080p.pack(anchor=tk.W, padx=20)

# Download folder selection
folder_button = tk.Button(root, text="Select Download Folder", command=select_download_folder)
folder_button.pack(pady=5)
folder_label = tk.Label(root, text="Download Folder: Not selected")
folder_label.pack(pady=5)

# Progress Label
progress_label = tk.Label(root, text="Progress: Video 0/0")
progress_label.pack(pady=5)

# Progress Bar with padding
progress_bar = ttk.Progressbar(root, length=400, mode='determinate')
progress_bar.pack(padx=20, pady=10)

# Download speed label
speed_label = tk.Label(root, text="Speed: N/A")
speed_label.pack(pady=5)

# Downloaded label
downloaded_label = tk.Label(root, text="Downloaded: 0")
downloaded_label.pack(pady=5)

# Remaining label
remaining_label = tk.Label(root, text="Remaining: 0")
remaining_label.pack(pady=5)

# Download button
download_button = tk.Button(root, text="Download", command=start_download)
download_button.pack(pady=20)

# Handle closing event
root.protocol("WM_DELETE_WINDOW", on_closing)

# Run the GUI
root.mainloop()
