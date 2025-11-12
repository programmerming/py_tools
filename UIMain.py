#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import asyncio
import threading
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from urllib.parse import urlparse, parse_qs
import sys
import os

import requests
from playwright.async_api import async_playwright
from playwright.sync_api import sync_playwright

"""Quark PDF 下载器 GUI 主程序"""
class QuarkPDFDownloader:
    def __init__(self, root):
        self.root = root
        self.root.title("Quark PDF 下载器")
        self.root.geometry("800x600")

        # 创建界面
        self.create_widgets()

        # 下载状态
        self.is_downloading = False

    def create_widgets(self):
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # URL输入框
        ttk.Label(main_frame, text="分享pdf文件列表链接(将下面链接替换成你的链接进行下载):").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.url_entry = ttk.Entry(main_frame, width=70)
        self.url_entry.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        self.url_entry.insert(0, "https://pan.quark.cn/s/bdcd6bbba908#/list/share/0905cef97a8b484ca1e4e794c631ace3")

        # 按钮框架
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=4, column=0, columnspan=2, pady=10)

        # 开始下载按钮
        self.start_button = ttk.Button(button_frame, text="开始下载", command=self.start_download)
        self.start_button.pack(side=tk.LEFT, padx=5)

        # 停止按钮
        self.stop_button = ttk.Button(button_frame, text="停止", command=self.stop_download, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5)

        # 日志显示区域
        ttk.Label(main_frame, text="日志信息:").grid(row=5, column=0, sticky=tk.W, pady=(10, 5))
        self.log_text = scrolledtext.ScrolledText(main_frame, height=20, width=90)
        self.log_text.grid(row=6, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)

        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(6, weight=1)

    def log_message(self, message):
        """在日志区域显示消息"""
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()

    def start_download(self):
        """开始下载"""
        if self.is_downloading:
            return

        share_url = self.url_entry.get().strip()

        if not share_url:
            messagebox.showerror("错误", "请输入分享链接")
            return

        self.is_downloading = True
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)

        # 在新线程中运行下载任务
        download_thread = threading.Thread(target=self.run_async_download,
                                           args=(share_url, "fetch_share_full_path"),
                                           daemon=True)
        download_thread.start()

    def stop_download(self):
        """停止下载"""
        self.is_downloading = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.log_message("下载已停止")

    def run_async_download(self, share_url, find_url):
        """运行异步下载任务"""
        try:
            # 确保Playwright浏览器已安装
            self.ensure_playwright_browsers()
            asyncio.run(self.get_pdf_preview_url(share_url, find_url))
        except Exception as e:
            self.log_message(f"下载出错: {str(e)}")
        finally:
            self.is_downloading = False
            self.root.after(0, lambda: self.start_button.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.stop_button.config(state=tk.DISABLED))

    def ensure_playwright_browsers(self):
        """确保Playwright浏览器已安装"""
        try:
            self.log_message("检查Playwright浏览器...")
            with sync_playwright() as p:
                # 尝试启动浏览器以触发自动下载
                p.chromium.launch(headless=True).close()
                self.log_message("Playwright浏览器已就绪")
        except Exception as e:
            self.log_message(f"Playwright浏览器初始化失败: {str(e)}")
            self.log_message("正在尝试安装浏览器...")
            try:
                # 如果在打包环境中，尝试手动安装
                from playwright._impl._driver import compute_driver_executable
                import subprocess
                driver_executable = compute_driver_executable()
                subprocess.run([driver_executable, "install", "chromium"], check=True)
                self.log_message("Playwright浏览器安装完成")
            except Exception as install_error:
                self.log_message(f"浏览器安装失败: {str(install_error)}")

    # 以下是您原有的函数，稍作修改以适配UI
    def get_download_url(self, preview_url):
        """请求 pdf_preview 接口，提取 download_url"""
        resp = requests.get(preview_url)
        resp.raise_for_status()
        data = resp.json()
        try:
            return data["data"]["download_url"]
        except Exception:
            raise Exception(f"返回数据里没有 download_url: {data}")

    def download_file(self, url, filename):
        """下载文件"""
        self.log_message(f"开始下载: {filename}")
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            total = int(r.headers.get("Content-Length", 0))
            with open(filename, "wb") as f:
                downloaded = 0
                downloadedMsgIndex = 0
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total:
                            percent = downloaded / total * 100
                            if percent / 33 > downloadedMsgIndex:
                                downloadedMsgIndex += 1
                                self.log_message(f"已下载 {downloaded}/{total} ({percent:.2f}%)")
                            if percent >= 100:
                                self.log_message(f"已下载 {downloaded}/{total} ({percent:.2f}%)")
            self.log_message(f"\n下载完成: {filename}")

    def build_preview_url(self, base_url, fid_token=""):
        """
        构建完整的PDF预览链接
        """
        # 解析URL和查询参数
        parsed_url = urlparse(base_url)
        query_params = parse_qs(parsed_url.query)

        # 更新fid_token参数
        if fid_token:
            query_params['fid_token'] = [fid_token]
        else:
            query_params['fid_token'] = ['']

        # 重新构建查询字符串
        from urllib.parse import urlencode
        new_query = urlencode(query_params, doseq=True)

        # 构建完整URL
        new_url = parsed_url._replace(query=new_query).geturl()

        return new_url

    async def get_pdf_preview_url(self, share_url, find_url=None):
        async with async_playwright() as p:
            # 添加错误处理
            try:
                browser = await p.chromium.launch(headless=True)
            except Exception as e:
                self.log_message(f"启动浏览器失败: {str(e)}")
                self.log_message("尝试重新安装浏览器...")
                raise e

            page = await browser.new_page()

            pdf_preview_url = None
            pdf_share_fid_token = None
            pdf_preview_real_url = ""

            def handle_response(response):
                nonlocal pdf_preview_url
                nonlocal pdf_preview_real_url
                url = response.url
                if find_url and find_url in url and pdf_preview_url is None:
                    pdf_preview_url = url
                    print(f"url-207:{url}")
                if "pdf_preview" in url:
                    print(f"url-209:{url}")
                    pdf_preview_real_url = self.build_preview_url(url, pdf_share_fid_token)

            page.on("response", handle_response)

            self.log_message(f"打开页面: {share_url}")
            await page.goto(share_url, wait_until="networkidle")

            # 等待一会，确保请求出现
            await asyncio.sleep(5)

            share_url_prefix = share_url.split("#")[0]

            if pdf_preview_url:
                self.log_message(f"获取到pdf文件列表的文件信息")
                resp = requests.get(pdf_preview_url)
                if resp.status_code == 200:
                    data = resp.json()
                    if data["code"] == 0:
                        pdf_urls = data["data"]["list"]

                        # 等待一会，确保请求出现
                        await asyncio.sleep(5)

                        # pdf文件列表
                        hasDownloaded = 0
                        for pdf_url in pdf_urls:
                            if not self.is_downloading:  # 检查是否已停止
                                break

                            pdf_url_fid = pdf_url["fid"]
                            pdf_url_file_name = pdf_url["file_name"]
                            if not pdf_url_file_name.lower().endswith(".pdf"):
                                continue
                            pdf_share_fid_token = pdf_url["share_fid_token"]

                            new_pdf_url = share_url_prefix + "#/share/docpdf/" + pdf_url_fid

                            print(f"new_pdf_url:{new_pdf_url}")
                            await page.goto(new_pdf_url, wait_until="networkidle")

                            # 等待一会，确保请求出现
                            await asyncio.sleep(5)

                            if not pdf_preview_real_url:
                                continue

                            # 获取到实际pdf的下载链接进行下载
                            resp = requests.get(pdf_preview_real_url)
                            print(pdf_preview_real_url)
                            if resp.status_code == 200:
                                data = resp.json()
                                if data["code"] == 0:
                                    download_url = data["data"]["download_url"]
                                    self.log_message(f"获取到文件下载信息")
                                    self.download_file(download_url, pdf_url_file_name)
                                    hasDownloaded += 1
                                else:
                                    self.log_message(f"请求失败: {data}")
                            else:
                                self.log_message(f"{pdf_preview_real_url}请求失败: {resp}")
                        self.log_message(f"{hasDownloaded}个pdf文件已全部下载完成！")
                    else:
                        self.log_message(f"请求失败: {data}")
            await browser.close()
            return pdf_preview_url


def main():
    root = tk.Tk()
    app = QuarkPDFDownloader(root)
    root.mainloop()


if __name__ == "__main__":
    main()
