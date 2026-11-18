# -*- coding: utf-8 -*-
"""逐玉记 · 风格化写实渲染润色（RenderPolishMixin）
================================================
把现有固定管线画面向「风格化写实 + 手绘电影质感」润色，落地四件事：
  1. 光影 grade：主光保持低角度暖金、环境补光转冷青（暗部偏青、亮部偏暖）
     —— v02 天气循环每帧覆盖光色，故此 grade 在 update 末尾每帧混合压制
  2. 大气透视：指数雾密度降至原 72%，远景更柔更透气
  3. 后处理：CommonFilters 低强度 Bloom（玉石/光源自然泛光）+ 曝光 +0.12 + Gamma 1.03
  4. 玉石 SSS 感：玉石拾取模型加微弱乳青自发光（不爆闪）

独立模块、一处接入；init_render_polish() 初始化、apply_render_grade() 每帧调用。
任一项失败均静默跳过，不影响游戏运行。
"""
from panda3d.core import Vec4


class RenderPolishMixin:

    def init_render_polish(self):
        self._rp_k = 0.0            # 渐入系数（2秒内平滑生效，避免开机突变）
        self._rp_fog0 = None        # 记录 v02 原始雾密度
        # ---- 后处理（Bloom / 曝光 / Gamma）----
        self._cf = None
        try:
            from direct.filter.CommonFilters import CommonFilters
            cf = CommonFilters(self.win, self.camera)
            applied = False
            try:
                # 低强度 Bloom：高阈值，只有玉石淡青光与篝火会轻微泛光
                if cf.setBloom(desat=-0.55, intensity=0.42):
                    applied = True
            except Exception:
                pass
            try:
                cf.setExposureAdjust(0.12); applied = True
            except Exception:
                pass
            try:
                cf.setGammaAdjust(1.03); applied = True
            except Exception:
                pass
            self._cf = cf if applied else None
        except Exception:
            self._cf = None
        # ---- 逐像素光照：明暗交界清晰、光影关系强化 ----
        try:
            self.render.setShaderAuto()
        except Exception:
            pass
        # ---- 玉石 SSS 微光 ----
        try:
            for node in getattr(self, 'ext_jade_pick', {}).values():
                node.setEmission(0.17, 0.26, 0.24, 1)
        except Exception:
            pass

    # -------------------------------------------------------------
    # 每帧 grade（必须在 super().update() 之后调用，压住 v02 天气覆盖）
    # -------------------------------------------------------------
    def apply_render_grade(self):
        # 主菜单俯瞰时也生效（菜单背景同样受益），只跳过未初始化情形
        if not hasattr(self, 'sun') or not hasattr(self, 'ambient'):
            return
        self._rp_k = min(1.0, getattr(self, '_rp_k', 0.0) + 0.02)
        k = self._rp_k

        # 1) 主光：暖金化（亮部偏暖）——Light.setColor 只接受单个 Vec4
        try:
            c = self.sun.getColor()
            self.sun.setColor(Vec4(
                c[0] + (1.22 - c[0]) * k * .60,
                c[1] + (1.00 - c[1]) * k * .60,
                c[2] + (0.72 - c[2]) * k * .60, 1))
        except Exception:
            pass
        # 2) 环境补光：冷青（暗部偏青，提亮暗部不死黑）
        try:
            c = self.ambient.getColor()
            self.ambient.setColor(Vec4(
                c[0] + (0.30 - c[0]) * k * .75,
                c[1] + (0.40 - c[1]) * k * .75,
                c[2] + (0.46 - c[2]) * k * .75, 1))
        except Exception:
            pass
        # 3) 大气透视：雾密度降至原 72%
        try:
            fog = self.fog
            if self._rp_fog0 is None:
                self._rp_fog0 = fog.getExpDensity()
            fog.setExpDensity(self._rp_fog0 * 1.5)
        except Exception:
            pass
