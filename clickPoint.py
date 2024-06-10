#coding:utf-8

import sys, codecs, jarray
from os import path, getenv

from java.awt import (
    Toolkit, Robot, Rectangle, BorderLayout, Cursor, Color, Font, BasicStroke, Insets,
    RenderingHints
    )
from java.awt.image import RescaleOp, BufferedImage
from java.awt.event import (
    MouseAdapter, MouseMotionAdapter, MouseEvent, MouseListener, MouseMotionListener, KeyEvent,
    ActionListener, ActionEvent
    )
from java.awt.event.MouseEvent import BUTTON1, BUTTON3
from javax.swing import (
    JDialog, JPanel, JFrame, BorderFactory, JPopupMenu, JMenu, JMenuItem,
    SwingUtilities, ToolTipManager
    )
from java.util import Timer, TimerTask
from java.lang import Runnable
from java.util.concurrent import TimeUnit
from java.awt.datatransfer import DataFlavor

FONT_JP = 'VL Gothic Regular'

clipboard = Toolkit.getDefaultToolkit().getSystemClipboard()
robot = Robot()
screenSize = Toolkit.getDefaultToolkit().getScreenSize()

class Guide(object):
    def __init__(self):
        self.image = BufferedImage(1024, 256, BufferedImage.TYPE_4BYTE_ABGR)
        self.graph = self.image.getGraphics()
        self.graph.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON)
        self.graph.setBackground(Color(1.0, 1.0, 1.0, 0.0))
        self.graph.clearRect(0, 0, 1024, 256)
        self.graph.setColor(Color(1.0, 1.0, 1.0, 0.5))
        self.graph.fillRoundRect(0, 0, 1024, 256, 30, 30)
        self.graph.setFont(Font(FONT_JP, Font.BOLD, 34))
        self.graph.setColor(Color(0.0, 0.0, 0.0, 0.5))
        self.graph.drawString(u'マウスをクリックして取得する座標を指定して下さい。', 48, 96);
        self.graph.drawString(u'右クリックでメニューを表示します。', 48, 176);

    def __get__(self, this, that):
        if this.validity:
            axes = this.supply()
            report = u'X座標：{0:>+5,d}px　     　Y座標：{1:>+5,d}px'
            self.graph.clearRect(0, 0, 1024, 256)
            self.graph.setColor(Color(1.0, 1.0, 1.0, 0.5))
            self.graph.fillRoundRect(0, 0, 1024, 256, 30, 30)
            self.graph.setColor(Color(0.0, 0.0, 0.0, 0.5))
            self.graph.drawString(report.format(*axes), 128, 96)
            self.graph.drawString(u'右クリックメニューによりセーブできます。', 128, 176);
        return self.image

class Overlay(JDialog):
    def __init__(self):
        super(self.__class__, self).__init__()
        self.setLocation(0, 0)
        self.setSize(screenSize)
        self.setUndecorated(True)
        self.setAlwaysOnTop(True)

class CtxMenu(JPopupMenu):
    def __init__(self, label): super(self.__class__, self).__init__(label)
    
    def show(self, client, pointX, pointY):
        super(self.__class__, self).show(client, pointX, pointY)
        axisX = pointX if pointX < client.width // 2 else pointX - self.width
        axisY = pointY if pointY < client.height // 2 else pointY - self.height
        self.setLocation(axisX, axisY)

ctx = CtxMenu(u'オフセットメニュー')

class MenuCtrl(JMenuItem):
    def __init__(self, label):
        super(self.__class__, self).__init__(label)
        self.setFont(Font(FONT_JP, Font.PLAIN, 16))
        self.setForeground(Color.DARK_GRAY)
        self.setMargin(Insets(5, 5, 5, 5))
        self.setSize(100, 30)

resetCtrl = MenuCtrl(u'リセット')
resetCtrl.setEnabled(False)

class resetImpl(ActionListener):
    def actionPerformed(self, ev):
        panel = ev.getSource().getParent().getInvoker()
        panel.pointX, panel.pointY = (int(panel.target.centerX), int(panel.target.centerY))
        panel.color = Color.WHITE
        panel.repaint()
        ev.getSource().setEnabled(False)

resetCtrl.addActionListener(resetImpl())

ctx.add(resetCtrl)
ctx.addSeparator()

cancelCtrl = MenuCtrl(u'キャンセル')

class cancelImpl(ActionListener):
    def actionPerformed(self, ev):
        panel = ev.getSource().getParent().getInvoker()
        window = panel.getTopLevelAncestor()
        window.dispose()
        panel.isBusy, panel.artifact, panel.validity = (False, None, False)

cancelCtrl.addActionListener(cancelImpl())

ctx.add(cancelCtrl)
ctx.addSeparator()

quitCtrl = MenuCtrl(u'セーブ')

class quitImpl(ActionListener):
    def actionPerformed(self, ev):
        panel = ev.getSource().getParent().getInvoker()
        window = panel.getTopLevelAncestor()
        window.dispose()
        panel.isBusy, panel.validity = (False, True)

quitCtrl.addActionListener(quitImpl())
ctx.add(quitCtrl)

class Telop(Runnable):
    def __init__(self, target, action):
        self.client, self.handler = (target, action)

    def lockOn(self):
        panel = self.client
        graph = self.client.getGraphics()
        graph.setColor(panel.color)
        graph.drawLine(panel.pointX, 0, panel.pointX, panel.getHeight())
        graph.drawLine(0, panel.pointY, panel.getWidth(), panel.pointY)

    def run(self):
        panel = self.client
        panel.color = Color.YELLOW
        w, h = (panel.getSize().width, panel.getSize().height)
        self.lockOn()
        x, y = ((w-1024)//2, (h-256)//2)
        graph = self.client.getGraphics()
        graph.drawImage(panel.sign, x, y, 1024, 256, None)
        TimeUnit.MILLISECONDS.sleep(1500)
        panel.color = Color.WHITE
        self.lockOn()
        panel.addMouseMotionListener(self.client)
        panel.addMouseListener(self.handler)

class PanelImpl(MouseAdapter):
    def __init__(self):
        super(self.__class__, self).__init__()
 
    def mousePressed(self, ev):
        if ev.getButton() == BUTTON1:
            panel = ev.getSource()
            panel.removeMouseListener(self)
            panel.removeMouseMotionListener(panel)
            panel.active, panel.validity = (False, True)
            point = ev.getPoint()
            resetCtrl.setEnabled(int(panel.target.centerX) != point.x or int(panel.target.centerY) != point.y)
            panel.pointX, panel.pointY = (point.x, point.y)
            self.color = Color(1.0, 1.0, 1.0, 0.0)
            panel.repaint()
            SwingUtilities.invokeLater(Telop(panel, self))
        ev.consume()
        
pImpl = PanelImpl()

class Content(JPanel, MouseMotionListener, Runnable):
    def __new__(cls, image, area, guide):
        cls.sign = guide
        return super(cls.__class__, cls).__new__(cls)

    def __init__(self, image, area, guide):
        super(JPanel, self).__init__(BorderLayout())
        self.setCursor(Cursor(Cursor.CROSSHAIR_CURSOR))
        self.target, self.isBusy, self.active, self.validity, self.color = (area, True, False, False, Color.YELLOW)
        self.backend = BufferedImage(image.getWidth(), image.getHeight(), image.getType())
        operator = RescaleOp(0.7, 0.0, None)
        operator.filter(image, self.backend)
        self.pointX, self.pointY = (int(area.centerX), int(area.centerY))
        clip = image.getSubimage(self.target.x, self.target.y, self.target.width, self.target.height)
        graph = self.backend.getGraphics()
        graph.drawImage(clip, self.target.x, self.target.y, self.target.width, self.target.height, None)

    def paintComponent(self, graph):
        self.setSize(self.backend.getWidth(), self.backend.getHeight())
        graph.setStroke(BasicStroke(1))
        graph.drawImage(self.backend, 0, 0, self.getWidth(), self.getHeight(), None)
        graph.setColor(self.color)
        graph.drawLine(self.pointX, 0, self.pointX, self.getHeight())
        graph.drawLine(0, self.pointY, self.getWidth(), self.pointY)
        graph.setColor(Color.LIGHT_GRAY)
        graph.drawRect(self.target.x, self.target.y, self.target.width, self.target.height)

    def supply(self):
        offset = (self.pointX-int(self.target.centerX), self.pointY-int(self.target.centerY))
        return jarray.array(offset, int) if self.validity else None

    def run(self): SwingUtilities.invokeLater(Telop(self, pImpl))

    def mouseDragged(self, ev):
        ev.consume()
        if not self.active:
            self.repaint()
            self.active = True

    def mouseMoved(self, ev):
        ev.consume()
        if not self.active:
            self.repaint()
            self.active = True

    def createToolTip(self):
        tips = super(self.__class__, self).createToolTip()
        tips.setFont(Font(FONT_JP, Font.PLAIN, 16))
        tips.setComponent(self)
        return tips

tipStats = ToolTipManager.sharedInstance()
tipStats.setDismissDelay(2000)
tipStats.setInitialDelay(300)
tipStats.setReshowDelay(2000)

def doRender(detect):
    deskImage = robot.createScreenCapture(Rectangle(screenSize))
    JDialog.setDefaultLookAndFeelDecorated(False)
    overlay = Overlay()
    content = Content(deskImage, detect, Guide())
    content.setComponentPopupMenu(ctx)
    content.setToolTipText(u'左クリックで座標設定 / 右クリックでメニュー表示')
    overlay.add(content, BorderLayout.CENTER)
    overlay.setVisible(True)
    TimeUnit.MILLISECONDS.sleep(500)
    SwingUtilities.invokeLater(content)
    while content.isBusy: TimeUnit.SECONDS.sleep(1)
    return content.supply()
