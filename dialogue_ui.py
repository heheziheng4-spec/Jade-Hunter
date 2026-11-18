# -*- coding: utf-8 -*-
"""沙光良渚 · 对话界面（Panda3D）

DialogueUIMixin：混入 Demo 类，提供对话框/选项按钮/好感度反馈。
依赖：dialogue.ENGINE（全局对话引擎），宿主需有 self.font / self.render / self.accept / self.dialog。
"""
from direct.gui.OnscreenText import OnscreenText
from direct.gui.DirectGui import DirectFrame, DirectButton
from panda3d.core import TextNode
import dialogue as DLG


class DialogueUIMixin:
    """与对话系统交互的界面层。调用 init_dialogue_ui() 初始化。"""

    def init_dialogue_ui(self):
        self.dlg_engine = DLG.ENGINE
        self.dlg_engine.set_state(getattr(self, 'state', None))
        self.in_conversation = False
        self.dlg_char = None
        self._dlg_options = []
        self.dlg_frame = DirectFrame(
            frameColor=(.10, .11, .09, .94), frameSize=(-1.15, 1.15, -.62, .62),
            pos=(0, 0, -.06), sortOrder=100)
        self.dlg_speaker = OnscreenText(
            parent=self.dlg_frame, text='', font=self.font, pos=(-1.02, .44),
            align=TextNode.ALeft, scale=.052, fg=(1, .86, .52, 1), mayChange=True)
        self.dlg_affinity = OnscreenText(
            parent=self.dlg_frame, text='', font=self.font, pos=(1.02, .46),
            align=TextNode.ARight, scale=.032, fg=(.55, .95, .75, 1), mayChange=True)
        self.dlg_text = OnscreenText(
            parent=self.dlg_frame, text='', font=self.font, pos=(-1.02, .24),
            align=TextNode.ALeft, scale=.036, wordwrap=54, fg=(.96, .93, .82, 1), mayChange=True)
        self.dlg_feedback = OnscreenText(
            parent=self.dlg_frame, text='', font=self.font, pos=(0, -.46),
            align=TextNode.ACenter, scale=.030, fg=(.6, 1, .72, 1), mayChange=True)
        self.dlg_buttons = []
        for i in range(4):
            b = DirectButton(
                parent=self.dlg_frame, text='', text_font=self.font, scale=.036,
                pos=(-.98, 0, -.02 - i * .105), frameColor=(.30, .29, .20, 1),
                text_fg=(1, .95, .80, 1), command=self._dlg_pick, extraArgs=[i],
                sortOrder=101)
            self.dlg_buttons.append(b)
        self.dlg_frame.hide()

    def start_dialogue(self, char_key):
        if not hasattr(self, 'dlg_engine'):
            self.init_dialogue_ui()
        node = self.dlg_engine.start(char_key)
        self.dlg_char = char_key
        self.in_conversation = True
        self.dialog = True
        self.keys.clear()
        self._dlg_show(node, feedback=None)

    def _dlg_show(self, node, feedback):
        ch = DLG.CHARACTERS.get(node.speaker)
        name = ch.name if ch else node.speaker
        self.dlg_speaker.setText(name)
        aff = self.dlg_engine.affinity.get(node.speaker, 0)
        label = self.dlg_engine.affinity_label(node.speaker)
        self.dlg_affinity.setText(f'好感 {aff} · {label}')
        self.dlg_text.setText(node.text)
        self.dlg_feedback.setText(feedback or '')
        opts = self.dlg_engine.visible_options(node)
        for i, b in enumerate(self.dlg_buttons):
            if i < len(opts):
                b.setText(f'{i+1}. {opts[i].text}')
                b.show()
            else:
                b.hide()
        self._dlg_options = opts
        self.dlg_frame.show()

    def _dlg_pick(self, index):
        if not self.in_conversation: return
        opts = getattr(self, '_dlg_options', [])
        if index >= len(opts): return
        opt = opts[index]
        nxt = self.dlg_engine.choose(opt)
        feedback = opt.reply or ''
        if opt.affinity:
            sign = '+' if opt.affinity > 0 else ''
            feedback += f'   [好感 {sign}{opt.affinity}]'
        if nxt is None:
            self.end_dialogue(feedback)
        else:
            self._dlg_show(nxt, feedback)

    def end_dialogue(self, feedback=''):
        self.in_conversation = False
        self.dialog = False
        self.dlg_frame.hide()
        if feedback:
            self.toast = feedback.replace('[', '').replace(']', '')
            self.toasting = 6
            if hasattr(self, 'message'): self.message.setText(self.toast)
        if hasattr(self, 'sync_ui'): self.sync_ui()

    def bind_dialogue_keys(self):
        for i in range(4):
            self.accept(str(i + 1), self._dlg_pick, [i])
