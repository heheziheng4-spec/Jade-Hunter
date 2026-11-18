# -*- coding: utf-8 -*-
"""逐玉记 · 一键推送到 GitHub / Gitee
双击运行，粘贴你在网页上创建的【空仓库地址】，自动完成推送并给出源码链接。
"""
import os, sys, subprocess, tkinter as tk
from tkinter import messagebox, simpledialog

HERE = os.path.dirname(os.path.abspath(__file__))


def run(cmd):
    r = subprocess.run(cmd, cwd=HERE, shell=True, capture_output=True, text=True, encoding='utf-8', errors='replace')
    return r.returncode, (r.stdout or '') + (r.stderr or '')


def main():
    root = tk.Tk(); root.withdraw()
    # 检查就绪
    code, log = run('git rev-parse --is-inside-work-tree')
    if code != 0:
        messagebox.showerror('错误', '未找到 Git 仓库。')
        return
    code, log = run('git log --oneline -1')
    if code != 0:
        messagebox.showerror('错误', '仓库还没有提交。')
        return

    url = simpledialog.askstring(
        '推送到 GitHub / Gitee',
        '请先到 GitHub 或 Gitee 网页创建一个新的【空仓库】\n'
        '（不要勾选 README / .gitignore / License，保持完全空）\n\n'
        '然后复制仓库地址，粘贴到下面：\n'
        '例：https://github.com/你的用户名/zhuyuji.git\n'
        '或：https://gitee.com/你的用户名/zhuyuji.git',
        initialvalue='')
    if not url:
        return
    url = url.strip()

    # 设置 remote
    run('git remote remove origin')
    code, log = run('git remote add origin "%s"' % url)
    if code != 0:
        messagebox.showerror('失败', '设置远程仓库失败：\n' + log[-800:])
        return

    messagebox.showinfo('提示', '即将推送约 235MB 数据，请耐心等待。\n'
                        '若弹出登录窗口，请输入你的代码托管平台账号密码 / Token。\n'
                        '推送完成后会弹窗告知。')

    code, log = run('git push -u origin master')
    if code == 0:
        web = url.replace('.git', '').replace('git@github.com:', 'https://github.com/')
        messagebox.showinfo('推送成功！',
                            '源码已推送到仓库。\n\n你的源码链接：\n' + web +
                            '\n\n打开这个链接，别人就能看到并下载你的游戏源码。')
        with open(os.path.join(HERE, '仓库链接.txt'), 'w', encoding='utf-8') as f:
            f.write('你的源码仓库链接：\n' + web + '\n')
    else:
        messagebox.showerror('推送失败',
                             '可能原因：账号未登录、仓库非空、网络问题。\n\n' + log[-1500:])


if __name__ == '__main__':
    main()
