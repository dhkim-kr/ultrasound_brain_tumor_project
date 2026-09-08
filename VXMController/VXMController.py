import sys
import os
import unittest
import logging
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
from slicer.util import VTKObservationMixin

import serial

"""
try:
    import matplotlib
except ModuleNotFoundError:
    subprocess.check_call(["sudo", sys.executable, "-m", "pip", "install", matplotlib])
    import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt
"""
import time, timeit
import random
import numpy as np

current_path = os.path.dirname(__file__)
sys.path.append(current_path + '/Submodule')
import Oscilloscope as osc


#
# VXMController
#

class VXMController(ScriptedLoadableModule):
    """Uses ScriptedLoadableModule base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        self.parent.title = "VXM Controller"  # TODO: make this more human readable by adding spaces
        self.parent.categories = [
            "Mymodule"]  # TODO: set categories (folders where the module shows up in the module selector)
        self.parent.dependencies = []  # TODO: add here list of module names that this module requires
        self.parent.contributors = [
            "Daehyeon Kim (KIST & Kwangwoon Univ.)"]  # TODO: replace with "Firstname Lastname (Organization)"
        # TODO: update with short description of the module and a link to online module documentation
        self.parent.helpText = """
Velmex stage control and oscilloscope acquisition for spatial ultrasound scanning.
See more information in <a href="https://github.com/dhkim-kr/ultrasound_brain_tumor_project">module documentation</a>.
"""
        # TODO: replace with organization, grant and thanks
        self.parent.acknowledgementText = """
This file was originally developed by Jean-Christophe Fillion-Robin, Kitware Inc., Andras Lasso, PerkLab,
and Steve Pieper, Isomics, Inc. and was partially funded by NIH grant 3P41RR013218-12S1.
"""


#
# VXMControllerWidget
#

class VXMControllerWidget(ScriptedLoadableModuleWidget, VTKObservationMixin):
    """Uses ScriptedLoadableModuleWidget base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

    def __init__(self, parent=None, Controller=None):
        """
    Called when the user opens the module the first time and the widget is initialized.
    """
        ScriptedLoadableModuleWidget.__init__(self, parent)
        VTKObservationMixin.__init__(self)  # needed for parameter node observation
        self.logic = None
        self._parameterNode = None
        self._updatingGUIFromParameterNode = False

        self.vmc = None # for VelmexController instance

        self.StepSize = None    # set the step size to move the velmex machine at once

        self.Xpos = None
        self.Ypos = None
        self.Zpos = None

        # 1D Find Max Point
        self.PLength = None  # Positive length
        self.NLength = None  # Negative length
        # for Move and 1D Find Max Point button
        self.FXButton = None # Find X button
        self.FYButton = None
        self.FZButton = None
        self.FMXButton = None  # Find Minus X Button
        self.FMYButton = None
        self.FMZButton = None

        # 2D Find Max Point
        self.TwoDPLength_1 = None  # Positive length on axis 0
        self.TwoDPLength_2 = None  # Positive length on axis 1
        self.TwoDNLength_1 = None  # Negative length on axis 0
        self.TwoDNLength_2 = None  # Negative length on axis 1
        # for 2D Find Max Point button
        self.FXYButton = None
        self.FYZButton = None
        self.FZXButton = None

        # 3D Find Max Point
        self.ThreeDPLength_1 = None  # Positive length on axis 0
        self.ThreeDPLength_2 = None  # Positive length on axis 1
        self.ThreeDPLength_3= None  # Positive length on axis 2
        self.ThreeDNLength_1 = None  # Negative length on axis 0
        self.ThreeDNLength_2 = None  # Negative length on axis 0
        self.ThreeDNLength_3 = None  # Negative length on axis 0
        self.ThreeDFindMaxPointButton = None  # for 3D Find Max Point button

        # 1D Scan
        self.PValue = None  # Positive value
        self.NValue = None  # Negative value
        # for Move and 1D scan button
        self.XButton = None
        self.YButton = None
        self.ZButton = None
        self.MXButton = None # Minus Button
        self.MYButton = None
        self.MZButton = None

        # 2D Scan
        self.TwoDPValue_1 = None # Positive value on axis 0
        self.TwoDPValue_2 = None # Positive value on axis 1
        self.TwoDNValue_1 = None # Negative value on axis 0
        self.TwoDNValue_2 = None # Negative value on axis 1
        # for 2D scan button
        self.XYButton = None
        self.YZButton = None
        self.ZXButton = None

        # 3D Scan
        self.ThreeDPValue_1 = None # Positive value on axis 0
        self.ThreeDPValue_2 = None # Positive value on axis 1
        self.ThreeDPValue_3 = None # Positive value on axis 2
        self.ThreeDNValue_1 = None # Negative value on axis 0
        self.ThreeDNValue_2 = None # Negative value on axis 0
        self.ThreeDNValue_3 = None # Negative value on axis 0
        self.ThreeDScanButton = None # for 3D scan button

        # fiducial nodes
        self.FiducialSelector = None
        self.FiducialSelector2 = None

    def setup(self):
        """
    Called when the user opens the module the first time and the widget is initialized.
    """
        ScriptedLoadableModuleWidget.setup(self)
        """
            GUI Part
        """
        #################################################################################
        # VXM Controller (1D Move)                                                      #
        # Input - integer type :    Step size                                           #
        # Button - Move X axis, Y axis, Z axis                                          #
        #################################################################################
        ControllButton = ctk.ctkCollapsibleButton()
        ControllButton.text = "VXM Controller"
        self.layout.addWidget(ControllButton)
        ControllFormLayout = qt.QFormLayout(ControllButton)

        step = qt.QLabel("Step size:")
        step.setFixedWidth(100)
        self.StepSize = qt.QDoubleSpinBox()
        self.StepSize.setRange(-500, 500)
        self.StepSize.value = 1.00

        ControllLayout = qt.QHBoxLayout()
        ControllLayout.addWidget(step)
        ControllLayout.addWidget(self.StepSize)
        ControllFormLayout.addRow(ControllLayout)

        self.XButton = qt.QPushButton("Move X")
        self.XButton.toolTip = "Forward or Backward"
        self.XButton.enabled = True

        self.YButton = qt.QPushButton("Move Y")
        self.YButton.toolTip = "Left or Right"
        self.YButton.enabled = True

        self.ZButton = qt.QPushButton("Move Z")
        self.ZButton.toolTip = "Up or Down"
        self.ZButton.enabled = True

        self.MXButton = qt.QPushButton("Move -X")
        self.MXButton.toolTip = "Forward or Backward"
        self.MXButton.enabled = True

        self.MYButton = qt.QPushButton("Move -Y")
        self.MYButton.toolTip = "Left or Right"
        self.MYButton.enabled = True

        self.MZButton = qt.QPushButton("Move -Z")
        self.MZButton.toolTip = "Up or Down"
        self.MZButton.enabled = True

        ButtonLayout = qt.QHBoxLayout()
        ButtonLayout.addWidget(self.XButton)
        ButtonLayout.addWidget(self.YButton)
        ButtonLayout.addWidget(self.ZButton)
        ControllFormLayout.addRow(ButtonLayout)

        ButtonLayout2 = qt.QHBoxLayout()
        ButtonLayout2.addWidget(self.MXButton)
        ButtonLayout2.addWidget(self.MYButton)
        ButtonLayout2.addWidget(self.MZButton)
        ControllFormLayout.addRow(ButtonLayout2)

        # When clicking button, 2nd parameter(function) is called
        self.XButton.connect('clicked(bool)', self.Xmove)
        self.YButton.connect('clicked(bool)', self.Ymove)
        self.ZButton.connect('clicked(bool)', self.Zmove)
        self.MXButton.connect('clicked(bool)', self.MXmove)
        self.MYButton.connect('clicked(bool)', self.MYmove)
        self.MZButton.connect('clicked(bool)', self.MZmove)


        ###############################################################################
        # Place fiducial points on scan position and max point position              #
        # Input - integer type :   fiducial list 1, 2                                 #
        # Button - None                                                               #
        ###############################################################################
        selectFiducialNodeButton = ctk.ctkCollapsibleButton()
        selectFiducialNodeButton.text = "Fiducial List"
        self.layout.addWidget(selectFiducialNodeButton)
        selectFiducialNodeLayout = qt.QFormLayout(selectFiducialNodeButton)

        self.FiducialSelector = slicer.qMRMLNodeComboBox()
        self.FiducialSelector.nodeTypes = ["vtkMRMLMarkupsFiducialNode"]
        self.FiducialSelector.selectNodeUponCreation = True
        self.FiducialSelector.addEnabled = True
        self.FiducialSelector.renameEnabled = True
        self.FiducialSelector.editEnabled = True
        self.FiducialSelector.removeEnabled = True
        self.FiducialSelector.noneEnabled = False
        self.FiducialSelector.showHidden = False
        self.FiducialSelector.showChildNodeTypes = False
        self.FiducialSelector.setMRMLScene(slicer.mrmlScene)
        self.FiducialSelector.setToolTip("Pick the Fiducial Node")
        selectFiducialNodeLayout.addRow("Scan Fiducial Node: ", self.FiducialSelector)

        self.FiducialSelector2 = slicer.qMRMLNodeComboBox()
        self.FiducialSelector2.nodeTypes = ["vtkMRMLMarkupsFiducialNode"]
        self.FiducialSelector2.selectNodeUponCreation = True
        self.FiducialSelector2.addEnabled = True
        self.FiducialSelector2.renameEnabled = True
        self.FiducialSelector2.editEnabled = True
        self.FiducialSelector2.removeEnabled = True
        self.FiducialSelector2.noneEnabled = False
        self.FiducialSelector2.showHidden = False
        self.FiducialSelector2.showChildNodeTypes = False
        self.FiducialSelector2.setMRMLScene(slicer.mrmlScene)
        self.FiducialSelector2.setToolTip("Pick the Fiducial Node")
        selectFiducialNodeLayout.addRow("Maxpoint Fiducial Node: ", self.FiducialSelector2)

        ###############################################################################
        # 2D Find Max Point                                                           #
        # Input - integer type :    Positive step value 1,2 & Negative step value 1,2 #
        # Button - Find X-Y, Find Y-Z, Find Z-X plane                                 #
        ###############################################################################
        TwoDFindMaxPointButton = ctk.ctkCollapsibleButton()
        TwoDFindMaxPointButton.text = "2D Find Max Point"
        self.layout.addWidget(TwoDFindMaxPointButton)
        TwoDFindMaxPointFormLayout = qt.QFormLayout(TwoDFindMaxPointButton)

        positive_1 = qt.QLabel("P1")
        positive_1.setFixedWidth(20)
        self.TwoDPLength_1 = qt.QDoubleSpinBox()
        self.TwoDPLength_1.setRange(-500, 500)
        self.TwoDPLength_1.value = 5.00

        negative_1 = qt.QLabel("N1")
        negative_1.setFixedWidth(20)
        self.TwoDNLength_1 = qt.QDoubleSpinBox()
        self.TwoDNLength_1.setRange(-500, 500)
        self.TwoDNLength_1.value = 5.00

        TwoDFindMaxPointLayout = qt.QHBoxLayout()
        TwoDFindMaxPointLayout.addWidget(positive_1)
        TwoDFindMaxPointLayout.addWidget(self.TwoDPLength_1)
        TwoDFindMaxPointLayout.addWidget(negative_1)
        TwoDFindMaxPointLayout.addWidget(self.TwoDNLength_1)
        TwoDFindMaxPointFormLayout.addRow(TwoDFindMaxPointLayout)

        positive_2 = qt.QLabel("P2")
        positive_2.setFixedWidth(20)
        self.TwoDPLength_2 = qt.QDoubleSpinBox()
        self.TwoDPLength_2.setRange(-500, 500)
        self.TwoDPLength_2.value = 5.00

        negative_2 = qt.QLabel("N2")
        negative_2.setFixedWidth(20)
        self.TwoDNLength_2 = qt.QDoubleSpinBox()
        self.TwoDNLength_2.setRange(-500, 500)
        self.TwoDNLength_2.value = 5.00

        TwoDFindMaxPointLayout = qt.QHBoxLayout()
        TwoDFindMaxPointLayout.addWidget(positive_2)
        TwoDFindMaxPointLayout.addWidget(self.TwoDPLength_2)
        TwoDFindMaxPointLayout.addWidget(negative_2)
        TwoDFindMaxPointLayout.addWidget(self.TwoDNLength_2)
        TwoDFindMaxPointFormLayout.addRow(TwoDFindMaxPointLayout)

        self.XYButton = qt.QPushButton("Find X-Y")
        self.XYButton.toolTip = "Forward or Backward and Left or Right"
        self.XYButton.enabled = True

        self.YZButton = qt.QPushButton("Find Y-Z")
        self.YZButton.toolTip = "Left or Right and Up or Down"
        self.YZButton.enabled = True

        self.ZXButton = qt.QPushButton("Find Z-X")
        self.ZXButton.toolTip = "Up or Down and Forward or Backward"
        self.ZXButton.enabled = True

        ButtonLayout = qt.QHBoxLayout()
        ButtonLayout.addWidget(self.XYButton)
        ButtonLayout.addWidget(self.YZButton)
        ButtonLayout.addWidget(self.ZXButton)
        TwoDFindMaxPointFormLayout.addRow(ButtonLayout)

        self.XYButton.connect('clicked(bool)', self.XYTwoDFindMaxPoint)
        self.YZButton.connect('clicked(bool)', self.YZTwoDFindMaxPoint)
        self.ZXButton.connect('clicked(bool)', self.ZXTwoDFindMaxPoint)

        ################################################################################
        # 3D Find Max Point                                                            #
        # Input - integer type : Positive step value 1,2,3 & Negative step value 1,2,3 #
        # Button - Find X-Y-Z                                                          #
        ################################################################################
        XYZFindMaxPointButton = ctk.ctkCollapsibleButton()
        XYZFindMaxPointButton.text = "3D Find Max Point"
        self.layout.addWidget(XYZFindMaxPointButton)
        ThreeDFindMaxPointFormLayout = qt.QFormLayout(XYZFindMaxPointButton)

        positive_1 = qt.QLabel("P1")
        positive_1.setFixedWidth(20)
        self.ThreeDPLength_1 = qt.QDoubleSpinBox()
        self.ThreeDPLength_1.setRange(-500, 500)
        self.ThreeDPLength_1.value = 5.00

        negative_1 = qt.QLabel("N1")
        negative_1.setFixedWidth(20)
        self.ThreeDNLength_1 = qt.QDoubleSpinBox()
        self.ThreeDNLength_1.setRange(-500, 500)
        self.ThreeDNLength_1.value = 5.00

        ThreeDFindMaxPointLayout = qt.QHBoxLayout()
        ThreeDFindMaxPointLayout.addWidget(positive_1)
        ThreeDFindMaxPointLayout.addWidget(self.ThreeDPLength_1)
        ThreeDFindMaxPointLayout.addWidget(negative_1)
        ThreeDFindMaxPointLayout.addWidget(self.ThreeDNLength_1)
        ThreeDFindMaxPointFormLayout.addRow(ThreeDFindMaxPointLayout)

        positive_2 = qt.QLabel("P2")
        positive_2.setFixedWidth(20)
        self.ThreeDPLength_2 = qt.QDoubleSpinBox()
        self.ThreeDPLength_2.setRange(-500, 500)
        self.ThreeDPLength_2.value = 5.00

        negative_2 = qt.QLabel("N2")
        negative_2.setFixedWidth(20)
        self.ThreeDNLength_2 = qt.QDoubleSpinBox()
        self.ThreeDNLength_2.setRange(-500, 500)
        self.ThreeDNLength_2.value = 5.00

        ThreeDFindMaxPointLayout = qt.QHBoxLayout()
        ThreeDFindMaxPointLayout.addWidget(positive_2)
        ThreeDFindMaxPointLayout.addWidget(self.ThreeDPLength_2)
        ThreeDFindMaxPointLayout.addWidget(negative_2)
        ThreeDFindMaxPointLayout.addWidget(self.ThreeDNLength_2)
        ThreeDFindMaxPointFormLayout.addRow(ThreeDFindMaxPointLayout)

        positive_3 = qt.QLabel("P3")
        positive_3.setFixedWidth(20)
        self.ThreeDPLength_3 = qt.QDoubleSpinBox()
        self.ThreeDPLength_3.setRange(-500, 500)
        self.ThreeDPLength_3.value = 5.00

        negative_3 = qt.QLabel("N3")
        negative_3.setFixedWidth(20)
        self.ThreeDNLength_3 = qt.QDoubleSpinBox()
        self.ThreeDNLength_3.setRange(-500, 500)
        self.ThreeDNLength_3.value = 5.00

        ThreeDFindMaxPointLayout = qt.QHBoxLayout()
        ThreeDFindMaxPointLayout.addWidget(positive_3)
        ThreeDFindMaxPointLayout.addWidget(self.ThreeDPLength_3)
        ThreeDFindMaxPointLayout.addWidget(negative_3)
        ThreeDFindMaxPointLayout.addWidget(self.ThreeDNLength_3)
        ThreeDFindMaxPointFormLayout.addRow(ThreeDFindMaxPointLayout)

        self.ThreeDFindMaxPointButton = qt.QPushButton("3D Find Max Point")
        self.ThreeDFindMaxPointButton.toolTip = "3D Find Max Point button"
        self.ThreeDFindMaxPointButton.enabled = True

        ButtonLayout = qt.QHBoxLayout()
        ButtonLayout.addWidget(self.ThreeDFindMaxPointButton)
        ThreeDFindMaxPointFormLayout.addRow(ButtonLayout)

        self.ThreeDFindMaxPointButton.connect('clicked(bool)', self.XYZThreeDFindMaxPoint)


        ##############################################################################
        # 1D Scan                                                                    #
        # Input - integer type :    Positive step value, Negative step value         #
        # Button - Scan X, Scan Y, Scan Z                                            #
        ##############################################################################
        OneDScanButton = ctk.ctkCollapsibleButton()
        OneDScanButton.text = "1D Scan"
        self.layout.addWidget(OneDScanButton)
        OneDScanFormLayout = qt.QFormLayout(OneDScanButton)

        positive = qt.QLabel("P")
        positive.setFixedWidth(10)
        self.PValue = qt.QDoubleSpinBox()
        self.PValue.setRange(-500, 500)
        self.PValue.value = 5.00        # default : 5

        negative = qt.QLabel("N")
        negative.setFixedWidth(10)
        self.NValue = qt.QDoubleSpinBox()
        self.NValue.setRange(-500, 500)
        self.NValue.value = 5.00

        OneDScanLayout = qt.QHBoxLayout()
        OneDScanLayout.addWidget(positive)
        OneDScanLayout.addWidget(self.PValue)
        OneDScanLayout.addWidget(negative)
        OneDScanLayout.addWidget(self.NValue)
        OneDScanFormLayout.addRow(OneDScanLayout)

        self.XButton = qt.QPushButton("Scan X")
        self.XButton.toolTip = "Forward or Backward"
        self.XButton.enabled = True

        self.YButton = qt.QPushButton("Scan Y")
        self.YButton.toolTip = "Left or Right"
        self.YButton.enabled = True

        self.ZButton = qt.QPushButton("Scan Z")
        self.ZButton.toolTip = "Up or Down"
        self.ZButton.enabled = True

        ButtonLayout = qt.QHBoxLayout()
        ButtonLayout.addWidget(self.XButton)
        ButtonLayout.addWidget(self.YButton)
        ButtonLayout.addWidget(self.ZButton)
        OneDScanFormLayout.addRow(ButtonLayout)

        self.XButton.connect('clicked(bool)', self.XOneDScan)
        self.YButton.connect('clicked(bool)', self.YOneDScan)
        self.ZButton.connect('clicked(bool)', self.ZOneDScan)

        ###############################################################################
        # 2D Scan                                                                     #
        # Input - integer type :    Positive step value 1,2 & Negative step value 1,2 #
        # Button - Scan X-Y, Scan Y-Z, Scan Z-X plane                                 #
        ###############################################################################
        TwoDScanButton = ctk.ctkCollapsibleButton()
        TwoDScanButton.text = "2D Scan"
        self.layout.addWidget(TwoDScanButton)
        TwoDScanFormLayout = qt.QFormLayout(TwoDScanButton)

        positive_1 = qt.QLabel("P1")
        positive_1.setFixedWidth(20)
        self.TwoDPValue_1 = qt.QDoubleSpinBox()
        self.TwoDPValue_1.setRange(-500, 500)
        self.TwoDPValue_1.value = 5.00

        negative_1 = qt.QLabel("N1")
        negative_1.setFixedWidth(20)
        self.TwoDNValue_1 = qt.QDoubleSpinBox()
        self.TwoDNValue_1.setRange(-500, 500)
        self.TwoDNValue_1.value = 5.00

        TwoDScanLayout = qt.QHBoxLayout()
        TwoDScanLayout.addWidget(positive_1)
        TwoDScanLayout.addWidget(self.TwoDPValue_1)
        TwoDScanLayout.addWidget(negative_1)
        TwoDScanLayout.addWidget(self.TwoDNValue_1)
        TwoDScanFormLayout.addRow(TwoDScanLayout)

        positive_2 = qt.QLabel("P2")
        positive_2.setFixedWidth(20)
        self.TwoDPValue_2 = qt.QDoubleSpinBox()
        self.TwoDPValue_2.setRange(-500, 500)
        self.TwoDPValue_2.value = 5.00

        negative_2 = qt.QLabel("N2")
        negative_2.setFixedWidth(20)
        self.TwoDNValue_2 = qt.QDoubleSpinBox()
        self.TwoDNValue_2.setRange(-500, 500)
        self.TwoDNValue_2.value = 5.00

        TwoDScanLayout = qt.QHBoxLayout()
        TwoDScanLayout.addWidget(positive_2)
        TwoDScanLayout.addWidget(self.TwoDPValue_2)
        TwoDScanLayout.addWidget(negative_2)
        TwoDScanLayout.addWidget(self.TwoDNValue_2)
        TwoDScanFormLayout.addRow(TwoDScanLayout)

        self.XYButton = qt.QPushButton("Scan X-Y plane")
        self.XYButton.toolTip = "Forward or Backward and Left or Right"
        self.XYButton.enabled = True

        self.YZButton = qt.QPushButton("Scan Y-Z plane")
        self.YZButton.toolTip = "Left or Right and Up or Down"
        self.YZButton.enabled = True

        self.ZXButton = qt.QPushButton("Scan Z-X plane")
        self.ZXButton.toolTip = "Up or Down and Forward or Backward"
        self.ZXButton.enabled = True

        ButtonLayout = qt.QHBoxLayout()
        ButtonLayout.addWidget(self.XYButton)
        ButtonLayout.addWidget(self.YZButton)
        ButtonLayout.addWidget(self.ZXButton)
        TwoDScanFormLayout.addRow(ButtonLayout)

        self.XYButton.connect('clicked(bool)', self.XYTwoDScan)
        self.YZButton.connect('clicked(bool)', self.YZTwoDScan)
        self.ZXButton.connect('clicked(bool)', self.ZXTwoDScan)


        ################################################################################
        # 3D Scan                                                                      #
        # Input - integer type : Positive step value 1,2,3 & Negative step value 1,2,3 #
        # Button - Scan X-Y-Z                                                          #
        ################################################################################
        XYZScanButton = ctk.ctkCollapsibleButton()
        XYZScanButton.text = "3D Scan"
        self.layout.addWidget(XYZScanButton)
        ThreeDScanFormLayout = qt.QFormLayout(XYZScanButton)

        positive_1 = qt.QLabel("P1")
        positive_1.setFixedWidth(20)
        self.ThreeDPValue_1 = qt.QDoubleSpinBox()
        self.ThreeDPValue_1.setRange(-500, 500)
        self.ThreeDPValue_1.value = 5.00

        negative_1 = qt.QLabel("N1")
        negative_1.setFixedWidth(20)
        self.ThreeDNValue_1 = qt.QDoubleSpinBox()
        self.ThreeDNValue_1.setRange(-500, 500)
        self.ThreeDNValue_1.value = 5.00

        ThreeDScanLayout = qt.QHBoxLayout()
        ThreeDScanLayout.addWidget(positive_1)
        ThreeDScanLayout.addWidget(self.ThreeDPValue_1)
        ThreeDScanLayout.addWidget(negative_1)
        ThreeDScanLayout.addWidget(self.ThreeDNValue_1)
        ThreeDScanFormLayout.addRow(ThreeDScanLayout)

        positive_2 = qt.QLabel("P2")
        positive_2.setFixedWidth(20)
        self.ThreeDPValue_2 = qt.QDoubleSpinBox()
        self.ThreeDPValue_2.setRange(-500, 500)
        self.ThreeDPValue_2.value = 5.00

        negative_2 = qt.QLabel("N2")
        negative_2.setFixedWidth(20)
        self.ThreeDNValue_2 = qt.QDoubleSpinBox()
        self.ThreeDNValue_2.setRange(-500, 500)
        self.ThreeDNValue_2.value = 5.00

        ThreeDScanLayout = qt.QHBoxLayout()
        ThreeDScanLayout.addWidget(positive_2)
        ThreeDScanLayout.addWidget(self.ThreeDPValue_2)
        ThreeDScanLayout.addWidget(negative_2)
        ThreeDScanLayout.addWidget(self.ThreeDNValue_2)
        ThreeDScanFormLayout.addRow(ThreeDScanLayout)

        positive_3 = qt.QLabel("P3")
        positive_3.setFixedWidth(20)
        self.ThreeDPValue_3 = qt.QDoubleSpinBox()
        self.ThreeDPValue_3.setRange(-500, 500)
        self.ThreeDPValue_3.value = 5.00

        negative_3 = qt.QLabel("N3")
        negative_3.setFixedWidth(20)
        self.ThreeDNValue_3 = qt.QDoubleSpinBox()
        self.ThreeDNValue_3.setRange(-500, 500)
        self.ThreeDNValue_3.value = 5.00

        ThreeDScanLayout = qt.QHBoxLayout()
        ThreeDScanLayout.addWidget(positive_3)
        ThreeDScanLayout.addWidget(self.ThreeDPValue_3)
        ThreeDScanLayout.addWidget(negative_3)
        ThreeDScanLayout.addWidget(self.ThreeDNValue_3)
        ThreeDScanFormLayout.addRow(ThreeDScanLayout)

        self.ThreeDScanButton = qt.QPushButton("3D Scan")
        self.ThreeDScanButton.toolTip = "3D scan button"
        self.ThreeDScanButton.enabled = True

        ButtonLayout = qt.QHBoxLayout()
        ButtonLayout.addWidget(self.ThreeDScanButton)
        ThreeDScanFormLayout.addRow(ButtonLayout)

        self.ThreeDScanButton.connect('clicked(bool)', self.XYZThreeDScan)


    """
        When Clicking above buttons, each correlated function is activated 
    """
    ###################################### 2D Find Max Point #######################################
    def XYTwoDFindMaxPoint(self):
        self.vmc = VelmexController()
        self.vmc.Setup()
        positive = [int(self.TwoDPValue_1.value/self.StepSize), int(self.TwoDPValue_2.value/self.StepSize)]
        negative = [int(self.TwoDNValue_1.value/self.StepSize), int(self.TwoDNValue_2.value/self.StepSize)]
        axis = [1, 2]
        self.FindTwoDMaxPoint(positive, negative, axis)
        self.vmc.resetXYZ()
        self.vmc.clear()

    def YZTwoDFindMaxPoint(self):
        self.vmc = VelmexController()
        self.vmc.Setup()
        positive = [int(self.TwoDPValue_1.value/self.StepSize), int(self.TwoDPValue_2.value/self.StepSize)]
        negative = [int(self.TwoDNValue_1.value/self.StepSize), int(self.TwoDNValue_2.value/self.StepSize)]
        axis = [2, 3]
        self.FindTwoDMaxPoint(positive, negative, axis)
        self.vmc.resetXYZ()
        self.vmc.clear()

    def ZXTwoDFindMaxPoint(self):
        self.vmc = VelmexController()
        self.vmc.Setup()
        positive = [int(self.TwoDPValue_1.value/self.StepSize), int(self.TwoDPValue_2.value/self.StepSize)]
        negative = [int(self.TwoDNValue_1.value/self.StepSize), int(self.TwoDNValue_2.value/self.StepSize)]
        axis = [3, 1]
        self.FindTwoDMaxPoint(positive, negative, axis)
        self.vmc.resetXYZ()
        self.vmc.clear()

    ###################################################################################

    ######################################### 3D Find Max Point ##################################################
    def XYZThreeDFindMaxPoint(self):
        self.vmc = VelmexController()
        self.vmc.Setup()
        positive = [int(self.ThreeDPValue_1.value/self.StepSize), int(self.ThreeDPValue_2.value/self.StepSize), int(self.ThreeDPValue_3.value/self.StepSize)]
        negative = [int(self.ThreeDNValue_1.value/self.StepSize), int(self.ThreeDNValue_2.value/self.StepSize), int(self.ThreeDNValue_3.value/self.StepSize)]
        axis = [1, 2, 3]
        self.FindThreeDMaxPoint(positive, negative, axis)
        self.vmc.resetXYZ()
        self.vmc.clear()
    ##############################################################################################################

    ########################## 1D Move ###################################
    def Xmove(self):
        if self.StepSize.value == 0:
            return  # There is no need to move.
        self.vmc = VelmexController() # instance initialization
        self.vmc.Setup()    # instance setup
        stepsize = self.vmc.setStepSize(self.StepSize.value) # set the step size
        if stepsize < 0:
            self.vmc.Nmove(-stepsize, 1) # negative move
        else:
            self.vmc.Pmove(stepsize, 1) # positive move
        self.vmc.clear() # instance clear

    def Ymove(self):
        if self.StepSize.value == 0:
            return

        self.vmc = VelmexController()
        self.vmc.Setup()
        print(self.StepSize.value)
        stepsize = self.vmc.setStepSize(self.StepSize.value)
        if stepsize < 0:
            self.vmc.Nmove(-stepsize, 2)
        else:
            self.vmc.Pmove(stepsize, 2)
        self.vmc.clear()

    def Zmove(self):
        if self.StepSize.value == 0:
            return

        self.vmc = VelmexController()
        self.vmc.Setup()
        stepsize = self.vmc.setStepSize(self.StepSize.value)
        if stepsize < 0:
            self.vmc.Nmove(-stepsize, 3)
        else:
            self.vmc.Pmove(stepsize, 3)
        self.vmc.clear()

    # Minus input value
    def MXmove(self):
        if self.StepSize.value == 0:
            return  # There is no need to move.
        self.vmc = VelmexController() # instance initialization
        self.vmc.Setup()    # instance setup
        stepsize = self.vmc.setStepSize(self.StepSize.value) # set the step size
        if stepsize < 0:
            self.vmc.Pmove(-stepsize, 1) # negative move
        else:
            self.vmc.Nmove(stepsize, 1) # positive move
        self.vmc.clear() # instance clear

    def MYmove(self):
        if self.StepSize.value == 0:
            return

        self.vmc = VelmexController()
        self.vmc.Setup()
        print(self.StepSize.value)
        stepsize = self.vmc.setStepSize(self.StepSize.value)
        if stepsize < 0:
            self.vmc.Pmove(-stepsize, 2)
        else:
            self.vmc.Nmove(stepsize, 2)
        self.vmc.clear()

    def MZmove(self):
        if self.StepSize.value == 0:
            return

        self.vmc = VelmexController()
        self.vmc.Setup()
        stepsize = self.vmc.setStepSize(self.StepSize.value)
        if stepsize < 0:
            self.vmc.Pmove(-stepsize, 3)
        else:
            self.vmc.Nmove(stepsize, 3)
        self.vmc.clear()
    #########################################################################

    ############################# 1D Scan #######################################
    def XOneDScan(self):
        self.vmc = VelmexController()
        self.vmc.Setup()
        self.OneDScan(int(self.PValue.value/self.StepSize.value), int(self.NValue.value/self.StepSize.value), 1)
        self.vmc.resetXYZ()
        self.vmc.clear()

    def YOneDScan(self):
        self.vmc = VelmexController()
        self.vmc.Setup()
        self.OneDScan(int(self.PValue.value/self.StepSize.value), int(self.NValue.value/self.StepSize.value), 2)
        self.vmc.resetXYZ()
        self.vmc.clear()

    def ZOneDScan(self):
        self.vmc = VelmexController()
        self.vmc.Setup()
        self.OneDScan(int(self.PValue.value/self.StepSize.value), int(self.NValue.value/self.StepSize.value), 3)
        self.vmc.resetXYZ()
        self.vmc.clear()
    #################################################################################

    ###################################### 2D Scan #######################################
    def XYTwoDScan(self):
        self.vmc = VelmexController()
        self.vmc.Setup()
        positive = [int(self.TwoDPValue_1.value/self.StepSize), int(self.TwoDPValue_2.value/self.StepSize)]
        negative = [int(self.TwoDNValue_1.value/self.StepSize), int(self.TwoDNValue_2.value/self.StepSize)]
        axis = [1, 2]
        self.TwoDScan(positive, negative, axis)
        self.vmc.resetXYZ()
        self.vmc.clear()

    def YZTwoDScan(self):
        self.vmc = VelmexController()
        self.vmc.Setup()
        positive = [int(self.TwoDPValue_1.value/self.StepSize), int(self.TwoDPValue_2.value/self.StepSize)]
        negative = [int(self.TwoDNValue_1.value/self.StepSize), int(self.TwoDNValue_2.value/self.StepSize)]
        axis = [2, 3]
        self.TwoDScan(positive, negative, axis)
        self.vmc.resetXYZ()
        self.vmc.clear()

    def ZXTwoDScan(self):
        self.vmc = VelmexController()
        self.vmc.Setup()
        positive = [int(self.TwoDPValue_1.value/self.StepSize), int(self.TwoDPValue_2.value/self.StepSize)]
        negative = [int(self.TwoDNValue_1.value/self.StepSize), int(self.TwoDNValue_2.value/self.StepSize)]
        axis = [3, 1]
        self.TwoDScan(positive, negative, axis)
        self.vmc.resetXYZ()
        self.vmc.clear()
    ###################################################################################

    #################################################### 3D Scan ##################################################
    def XYZThreeDScan(self):
        self.vmc = VelmexController()
        self.vmc.Setup()
        positive = [int(self.ThreeDPValue_1.value/self.StepSize), int(self.ThreeDPValue_2.value/self.StepSize), int(self.ThreeDPValue_3.value/self.StepSize)]
        negative = [int(self.ThreeDNValue_1.value/self.StepSize), int(self.ThreeDNValue_2.value/self.StepSize), int(self.ThreeDNValue_3.value/self.StepSize)]
        axis = [1, 2, 3]
        self.ThreeDScan(positive, negative, axis)
        self.vmc.resetXYZ()
        self.vmc.clear()
    ##############################################################################################################

    """
        Logic Part
        1. Find Max Point
        2. 1D scan
        3. 2D scan
        4. 3D scan
        5. GUI - To place fiducials on scanned positions and fiducial on max point
    """
    def FindOneDMaxPoint(self, plus, minus, axisparam):
        StepSize = self.vmc.setStepSize(minus * self.StepSize.value) # set the step size
        self.vmc.Nmove(StepSize, axisparam) # move to end
        self.vmc.setOneDXYZ(-minus * self.StepSize.value, axisparam) # for plot point
        self.placeScanFiducial(self.vmc.newx, self.vmc.newy, self.vmc.newz) # add fiducial

        OneStep = self.vmc.setStepSize(self.StepSize.value) # Only one step size

        findmaxV = np.zeros((plus + minus + 1, len(self.vmc.waveform)), float)  # store the data from Oscilloscope

        for p in range(plus + minus + 1): # 1D scan
            slicer.app.processEvents() # Dynamic updating scene
            self.vmc.waveform = osc.getData() # get the data from Oscilloscope
            findmaxV[p] = np.copy(self.vmc.waveform)  # store data
            if p != (plus + minus): # when it is not last step
                self.vmc.Pmove(OneStep, axisparam) # move one step
                self.vmc.setOneDXYZ(self.StepSize.value, axisparam)
                self.placeScanFiducial(self.vmc.newx, self.vmc.newy, self.vmc.newz)

        np.save(os.path.join(slicer.app.temporaryPath, "vxm_scan"),findmaxV)
        OneDArrayIdx = np.argmax(FindmaxV) + 1 # Flatten max value index
        maxVIdx = 0 # Real max value index
        print("Flatten: ", OneDArrayIdx)
        while OneDArrayIdx > 0:
            maxVIdx += 1
            OneDArrayIdx -= len(self.vmc.waveform)
        print("max index: ", maxVIdx)
        if maxVIdx == (plus + minus + 1): # when it is last step
            return maxVIdx # There is no need to go back
        StepToGoBack = plus + minus + 1 - maxVIdx # step count of machine to be moved
        StepSizeToGoBack = self.vmc.setStepSize(StepToGoBack * self.StepSize.value) # step size
        self.vmc.Nmove(StepSizeToGoBack, axisparam) # move
        self.vmc.setOneDXYZ(-StepToGoBack * self.StepSize.value, axisparam)
        self.placeMaxFiducial(self.vmc.newx, self.vmc.newy, self.vmc.newz)

        return maxVIdx

    def FindTwoDMaxPoint(self, plus, minus, axisparam):
        # Initializing the Properties of fiducial node
        self.setFiducialListProperties(self.FiducialSelector.currentNode(), True, [0, 0, 1])
        self.setFiducialListProperties(self.FiducialSelector2.currentNode(), True, [1, 0, 0])

        # First scan
        self.Xpos = self.FindOneDMaxPoint(plus[0], minus[0], axisparam[0])
        self.Ypos = self.FindOneDMaxPoint(plus[1], minus[1], axisparam[1])
        # length
        Xlength = plus[0] + minus[0] + 1
        Ylength = plus[1] + minus[1] + 1
        # old positions
        oldXpos = self.Xpos
        oldYpos = self.Ypos
        i = 1
        print("1 step Old X, Y : ", oldXpos, oldYpos)
        while True:
            i += 1
            # take turns scanning axis 0 & 1
            self.Xpos = self.FindOneDMaxPoint(Xlength - oldXpos, oldXpos - 1, axisparam[0])
            print("Xpos{}: ".format(i), self.Xpos)
            if oldXpos == self.Xpos:
                print("Yes Old same New X: ", oldXpos, self.Xpos)
                break
            self.Ypos = self.FindOneDMaxPoint(Ylength - oldYpos, oldYpos - 1, axisparam[1])
            print("Ypos{}: ".format(i), self.Ypos)
            if oldYpos == self.Ypos:
                print("Yes Old same New Y: ", oldYpos, self.Ypos)
                break
            oldXpos = self.Xpos
            oldYpos = self.Ypos
            print("step{} Old X, Y : ".format(i), oldXpos, oldYpos)
        print("lengthX,Y: ", Xlength, Ylength)
        print("posX,Y: ", oldXpos, oldYpos)

    def FindThreeDMaxPoint(self, plus, minus, axisparam):
        # Initializing the Properties of fiducial node
        self.setFiducialListProperties(self.FiducialSelector.currentNode(), True, [0, 0, 1])
        self.setFiducialListProperties(self.FiducialSelector2.currentNode(), True, [1, 0, 0])
        """
        TestMatrix = np.arange(1, 730, 1)
        np.random.shuffle(TestMatrix)
        TestMatrix = TestMatrix.reshape(9, 9,9)
        print(TestMatrix)
        print(np.argmax(TestMatrix) + 1)
        """
        # First scan
        self.Xpos = self.FindOneDMaxPoint(plus[0], minus[0], axisparam[0])
        self.Ypos = self.FindOneDMaxPoint(plus[1], minus[1], axisparam[1])
        self.Zpos = self.FindOneDMaxPoint(plus[2], minus[2], axisparam[2])
        # Length
        Xlength = plus[0] + minus[0] + 1
        Ylength = plus[1] + minus[1] + 1
        Zlength = plus[2] + minus[2] + 1
        # Old positions
        oldXpos = self.Xpos
        oldYpos = self.Ypos
        oldZpos = self.Zpos
        i = 1
        print("1 step Old X, Y : ", oldXpos, oldYpos)
        while True:
            i += 1
            self.Xpos = self.FindOneDMaxPoint(Xlength - oldXpos, oldXpos - 1, axisparam[0])
            print("Xpos{}: ".format(i), self.Xpos)

            self.Ypos = self.FindOneDMaxPoint(Ylength - oldYpos, oldYpos - 1, axisparam[1])
            print("Ypos{}: ".format(i), self.Ypos)
            if oldYpos == self.Ypos and oldXpos == self.Xpos:
                print("Yes Old same New X, Y: ")
                break

            self.Zpos = self.FindOneDMaxPoint(Zlength - oldZpos, oldZpos - 1, axisparam[2])
            print("Zpos{}: ".format(i), self.Zpos)

            oldXpos = self.Xpos
            oldYpos = self.Ypos
            oldZpos = self.Zpos
            print("step{} Old X, Y ,Z: ".format(i), oldXpos, oldYpos, oldZpos)
        print("lengthX,Y,Z: ", Xlength, Ylength, Zlength)
        print("posX,Y,Z: ", oldXpos, oldYpos, oldZpos)

    def OneDScan(self, plus, minus, axisparam):
        # Initializing the Properties of fiducial node
        self.setFiducialListProperties(self.FiducialSelector.currentNode(), True, [0, 0, 1])
        self.setFiducialListProperties(self.FiducialSelector2.currentNode(), True, [1, 0, 0])

        findmaxV = np.zeros((plus + minus + 1, len(self.vmc.waveform)), float) # store the data from Oscilloscope

        StepSize = self.vmc.setStepSize(minus*self.StepSize.value) # set step size
        self.vmc.Nmove(StepSize, axisparam) # move
        self.vmc.setOneDXYZ(-minus*self.StepSize.value, axisparam)
        self.placeScanFiducial(self.vmc.newx, self.vmc.newy, self.vmc.newz) # add fiducial

        OneStep = self.vmc.setStepSize(self.StepSize.value) # only one step
        for p in range(plus + minus + 1):
            self.vmc.waveform = osc.getData() # get data from Oscilloscope
            osc.print_data()
            findmaxV[p] = np.copy(self.vmc.waveform) # store data
            if p != (plus + minus):
                self.vmc.Pmove(OneStep, axisparam) # move one step
                self.vmc.setOneDXYZ(self.StepSize.value, axisparam)
                slicer.app.processEvents() # Dynamic updating scene
                self.placeScanFiducial(self.vmc.newx, self.vmc.newy, self.vmc.newz)

        # 2D array is converted to 1D array
        # and then index of maximum scala value is returned
        # ex) (2, 4000) is the maximum scala value on (7, 5000) matrix
        # then np.argmax() return 8999
        # so, we need to find the row index of location with maximum scala value
        print(findmaxV)
        np.save(os.path.join(slicer.app.temporaryPath, "vxm_scan"),findmaxV)
        OneDArrayIdx = np.argmax(findmaxV) + 1 # flatten max value index
        maxVIdx = 0 # real max value index
        print("Flatten: ", OneDArrayIdx)
        while OneDArrayIdx > 0:
            maxVIdx += 1
            OneDArrayIdx -= len(self.vmc.waveform)
        print("max index: ", maxVIdx)
        if maxVIdx == (plus + minus + 1): # it is the last step
            return maxVIdx # There is no need to move
        StepToGoBack = plus + minus + 1 - maxVIdx # step count of machine to be moved
        StepSizeToGoBack = self.vmc.setStepSize(StepToGoBack*self.StepSize.value) # step size to go back
        self.vmc.Nmove(StepSizeToGoBack, axisparam) # move
        self.vmc.setOneDXYZ(-StepToGoBack*self.StepSize.value, axisparam)
        self.placeMaxFiducial(self.vmc.newx, self.vmc.newy, self.vmc.newz)

        return maxVIdx

    def TwoDScan(self, plus, minus, axisparam):
        self.setFiducialListProperties(self.FiducialSelector.currentNode(), True, [0, 0, 1])
        self.setFiducialListProperties(self.FiducialSelector2.currentNode(), True, [1, 0, 0])

        findmaxV = np.zeros((plus[1] + minus[1] + 1, plus[0] + minus[0] + 1, len(self.vmc.waveform)), float)

        # need exception handling for negative or zero value of plus and minus
        StepSizeX = self.vmc.setStepSize(minus[0]*self.StepSize.value)
        StepSizeY = self.vmc.setStepSize(plus[1]*self.StepSize.value)
        self.vmc.Nmove(StepSizeX, axisparam[0])
        self.vmc.Pmove(StepSizeY, axisparam[1])

        self.vmc.setTwoDXYZ(-minus[0]*self.StepSize.value, plus[1]*self.StepSize.value, axisparam)
        self.placeScanFiducial(self.vmc.newx, self.vmc.newy, self.vmc.newz)

        OneStep = self.vmc.setStepSize(self.StepSize.value)
        for y in range(plus[1] + minus[1] + 1):
            for x in range(plus[0] + minus[0] + 1):
                slicer.app.processEvents()
                self.vmc.waveform = osc.getData()
                if y % 2 == 0:
                    findmaxV[y][x] = np.copy(self.vmc.waveform)
                    if x != (plus[0] + minus[0]):
                        self.vmc.Pmove(OneStep, axisparam[0])
                        self.vmc.setTwoDXYZ(self.StepSize.value, 0, axisparam)
                        self.placeScanFiducial(self.vmc.newx, self.vmc.newy, self.vmc.newz)
                else:
                    findmaxV[y][plus[0] + minus[0] - x] = np.copy(self.vmc.waveform)
                    if x != (plus[0] + minus[0]):
                        self.vmc.Nmove(OneStep, axisparam[0])
                        self.vmc.setTwoDXYZ(-self.StepSize.value, 0, axisparam)
                        self.placeScanFiducial(self.vmc.newx, self.vmc.newy, self.vmc.newz)
            if y != (plus[1] + minus[1]):
                self.vmc.Nmove(OneStep, axisparam[1])
                self.vmc.setTwoDXYZ(0, -self.StepSize.value, axisparam)
                self.placeScanFiducial(self.vmc.newx, self.vmc.newy, self.vmc.newz)

        # 2D array is converted to 1D array
        # and then index of maximum scala value is returned
        # ex) (2, 4000) is the maximum scala value on (7, 5000) matrix
        # then np.argmax() return 8999
        # so, we need to find the row index of location with maximum scala value
        maxVmatrix = np.max(findmaxV, axis=2)
        print(maxVmatrix)
        maxVidx_1 = np.argmax(maxVmatrix) + 1
        maxVidx_2 = 0
        print(maxVidx_1)
        np.save(os.path.join(slicer.app.temporaryPath, "vxm_scan"), findmaxV)
        while maxVidx_1 > 0:
            maxVidx_2 += 1
            maxVidx_1 -= plus[0] + minus[0] + 1
        maxVidx_1 += plus[0] + minus[0] + 1
        print(maxVidx_1)
        print(maxVidx_2)
        if (plus[1] + minus[1] + 1) % 2 == 1:
            if maxVidx_2 % 2 == 1:
                StepToGoBack_1 = plus[0] + minus[0] + 1 - maxVidx_1
            else:
                StepToGoBack_1 = maxVidx_1 - 1
            if StepToGoBack_1 != 0:
                StepSizeToGoBack_1 = self.vmc.setStepSize(StepToGoBack_1*self.StepSize.value)
                self.vmc.Nmove(StepSizeToGoBack_1, axisparam[0])
                self.vmc.setTwoDXYZ(-StepToGoBack_1*self.StepSize.value, 0, axisparam)

        else:
            if maxVidx_2 % 2 == 1:
                StepToGoBack_1 = maxVidx_1 - 1
            else:
                StepToGoBack_1 = plus[0] + minus[0] + 1 - maxVidx_1
            if StepToGoBack_1 != 0:
                StepSizeToGoBack_1 = self.vmc.setStepSize(StepToGoBack_1*self.StepSize.value)
                self.vmc.Pmove(StepSizeToGoBack_1, axisparam[0])
                self.vmc.setTwoDXYZ(StepToGoBack_1*self.StepSize.value, 0, axisparam)

        print("stepX", StepToGoBack_1)
        StepToGoBack_2 = plus[1] + minus[1] + 1 - maxVidx_2
        print("stepY", StepToGoBack_2)
        if StepToGoBack_2 != 0:
            StepSizeToGoBack_2 = self.vmc.setStepSize(StepToGoBack_2*self.StepSize.value)
            self.vmc.Pmove(StepSizeToGoBack_2, axisparam[1])
            self.vmc.setTwoDXYZ(0, StepToGoBack_2*self.StepSize.value, axisparam)
            self.placeMaxFiducial(self.vmc.newx, self.vmc.newy, self.vmc.newz)

    def ThreeDScan(self, plus, minus, axisparam):
        self.setFiducialListProperties(self.FiducialSelector.currentNode(), False, [0,0,1])
        self.setFiducialListProperties(self.FiducialSelector2.currentNode(), True, [1,0,0])

        findmaxV = np.zeros(
            (plus[2] + minus[2] + 1, plus[1] + minus[1] + 1, plus[0] + minus[0] + 1, len(self.vmc.waveform)), float)

        # need exception handling for negative or zero value of plus and minus
        StepSizeX = self.vmc.setStepSize(minus[0]*self.StepSize.value)
        StepSizeY = self.vmc.setStepSize(plus[1]*self.StepSize.value)
        StepSizeZ = self.vmc.setStepSize(minus[2]*self.StepSize.value)
        self.vmc.Nmove(StepSizeX, axisparam[0])
        self.vmc.Pmove(StepSizeY, axisparam[1])
        self.vmc.Nmove(StepSizeZ, axisparam[2])

        self.vmc.setThreeDXYZ(-minus[0]*self.StepSize.value, plus[1]*self.StepSize.value, -minus[2]*self.StepSize.value)
        self.placeScanFiducial(self.vmc.newx, self.vmc.newy, self.vmc.newz)
        self.createScanFiducialListByPlane(1)
        self.placeScanFiducialOnCreatedPlane(self.vmc.newx, self.vmc.newy, self.vmc.newz, 1)

        OneStep = self.vmc.setStepSize(self.StepSize.value)
        for z in range(plus[2] + minus[2] + 1):
            for y in range(plus[1] + minus[1] + 1):
                for x in range(plus[0] + minus[0] + 1):
                    slicer.app.processEvents()
                    self.vmc.waveform = osc.getData()
                    if y % 2 == 0:
                        findmaxV[z][y][x] = np.copy(self.vmc.waveform)
                        if x != (plus[0] + minus[0]):
                            self.vmc.Pmove(OneStep, axisparam[0])
                            self.vmc.setThreeDXYZ(self.StepSize.value, 0, 0)
                            self.placeScanFiducial(self.vmc.newx, self.vmc.newy, self.vmc.newz)
                            self.placeScanFiducialOnCreatedPlane(self.vmc.newx, self.vmc.newy, self.vmc.newz,z+1)
                    else:
                        findmaxV[z][y][plus[0] + minus[0] - x] = np.copy(self.vmc.waveform)
                        if x != (plus[0] + minus[0]):
                            self.vmc.Nmove(OneStep, axisparam[0])
                            self.vmc.setThreeDXYZ(-self.StepSize.value, 0, 0)
                            self.placeScanFiducial(self.vmc.newx, self.vmc.newy, self.vmc.newz)
                            self.placeScanFiducialOnCreatedPlane(self.vmc.newx, self.vmc.newy, self.vmc.newz, z + 1)
                if y != (plus[1] + minus[1]):
                    self.vmc.Nmove(OneStep, axisparam[1])
                    self.vmc.setThreeDXYZ(0, -self.StepSize.value, 0)
                    self.placeScanFiducial(self.vmc.newx, self.vmc.newy, self.vmc.newz)
                    self.placeScanFiducialOnCreatedPlane(self.vmc.newx, self.vmc.newy, self.vmc.newz, z + 1)

            if z != (plus[2] + minus[2]):
                StepSizeToGoBack_Y = self.vmc.setStepSize(y*self.StepSize.value)
                self.vmc.Pmove(StepSizeToGoBack_Y, axisparam[1])
                if y % 2 == 0:
                    self.vmc.setThreeDXYZ(-x*self.StepSize.value, y*self.StepSize.value, self.StepSize.value)
                    StepSizeToGoBack_X = self.vmc.setStepSize(x*self.StepSize.value)
                    self.vmc.Nmove(StepSizeToGoBack_X, axisparam[0])
                else:
                    self.vmc.setThreeDXYZ(0, y*self.StepSize.value, self.StepSize.value)
                self.vmc.Pmove(OneStep, axisparam[2])
                self.placeScanFiducial(self.vmc.newx, self.vmc.newy, self.vmc.newz)

                self.createScanFiducialListByPlane(z + 2)
                self.placeScanFiducialOnCreatedPlane(self.vmc.newx, self.vmc.newy, self.vmc.newz, z + 2)

                node_idx = z+1
                prev_node = slicer.util.getNode("sf_" + str(node_idx))
                prev_display_node = prev_node.GetDisplayNode()
                prev_display_node.SetVisibility(False)


        # 2D array is converted to 1D array
        # and then index of maximum scala value is returned
        # ex) (2, 4000) is the maximum scala value on (7, 5000) matrix
        # then np.argmax() return 8999
        # so, we need to find the row index of location with maximum scala value
        maxVmatrix = np.max(findmaxV, axis=3)
        print(maxVmatrix)
        maxVidx_1 = np.argmax(maxVmatrix) + 1
        maxVidx_2 = 0
        maxVidx_3 = 0
        np.save(os.path.join(slicer.app.temporaryPath, "vxm_scan"), findmaxV)
        print("X-Y-Z max index: ", maxVidx_1)
        while maxVidx_1 > 0:
            maxVidx_3 += 1
            maxVidx_1 -= ((plus[0] + minus[0] + 1) * (plus[1] + minus[1] + 1))
        maxVidx_1 += ((plus[0] + minus[0] + 1) * (plus[1] + minus[1] + 1))

        StepToGoBack_3 = plus[2] + minus[2] + 1 - maxVidx_3
        StepSizeToGoBack_3 = self.vmc.setStepSize(StepToGoBack_3*self.StepSize.value)
        self.vmc.Nmove(StepSizeToGoBack_3, axisparam[2])
        self.vmc.setThreeDXYZ(0, 0, -StepToGoBack_3*self.StepSize.value)

        print("X-Y plane max index: ", maxVidx_1)
        print("max Z index: ", maxVidx_3)

        while maxVidx_1 > 0:
            maxVidx_2 += 1
            maxVidx_1 -= plus[0] + minus[0] + 1
        maxVidx_1 += plus[0] + minus[0] + 1

        print("max X index: ", maxVidx_1)
        print("max Y index: ", maxVidx_2)
        if (plus[1] + minus[1] + 1) % 2 == 1:
            if maxVidx_2 % 2 == 1:
                StepToGoBack_1 = plus[0] + minus[0] + 1 - maxVidx_1
            else:
                StepToGoBack_1 = maxVidx_1 - 1
            if StepToGoBack_1 != 0:
                StepSizeToGoBack_1 = self.vmc.setStepSize(StepToGoBack_1*self.StepSize.value)
                self.vmc.Nmove(StepSizeToGoBack_1, axisparam[0])
                self.vmc.setThreeDXYZ(-StepToGoBack_1*self.StepSize.value, 0, 0)

        else:
            if maxVidx_2 % 2 == 1:
                StepToGoBack_1 = maxVidx_1 - 1
            else:
                StepToGoBack_1 = plus[0] + minus[0] + 1 - maxVidx_1
            if StepToGoBack_1 != 0:
                StepSizeToGoBack_1 = self.vmc.setStepSize(StepToGoBack_1*self.StepSize.value)
                self.vmc.Pmove(StepSizeToGoBack_1, axisparam[0])
                self.vmc.setThreeDXYZ(StepToGoBack_1*self.StepSize.value, 0, 0)

        print("stepX", StepToGoBack_1)
        StepToGoBack_2 = plus[1] + minus[1] + 1 - maxVidx_2
        print("stepY", StepToGoBack_2)
        print("stepZ", StepToGoBack_3)
        if StepToGoBack_2 != 0:
            StepSizeToGoBack_2 = self.vmc.setStepSize(StepToGoBack_2*self.StepSize.value)
            self.vmc.Pmove(StepSizeToGoBack_2, axisparam[1])
            self.vmc.setThreeDXYZ(0, StepToGoBack_2*self.StepSize.value, 0)
            self.placeMaxFiducial(self.vmc.newx, self.vmc.newy, self.vmc.newz)

        if maxVidx_3 == 1:
            print("Max point is on the {}st plane".format(maxVidx_3))
        elif maxVidx_3 == 2:
            print("Max point is on the {}nd plane".format(maxVidx_3))
        elif maxVidx_3 == 3:
            print("Max point is on the {}rd plane".format(maxVidx_3))
        else:
            print("Max point is on the {}th plane".format(maxVidx_3))

    def setFiducialListProperties(self, node, switch, color):
        fn = node # fn: fiducial node
        fn.SetLocked(True)
        dn = fn.GetDisplayNode() # dn: display node
        dn.SetVisibility(switch)
        dn.SetSelectedColor(color[0], color[1], color[2])

    def placeScanFiducial(self, x, y, z):
        fn = self.FiducialSelector.currentNode()
        fn.AddFiducial(x, y, z)

    def placeMaxFiducial(self, x, y, z):
        fn = self.FiducialSelector2.currentNode()
        fn.AddFiducial(x, y, z)

    def createScanFiducialListByPlane(self, idx):
        fn = slicer.vtkMRMLMarkupsFiducialNode() # fn: fiducial node
        slicer.mrmlScene.AddNode(fn)
        fn.SetName("sf_" + str(idx)) # sf: scan fiducial
        fn.SetLocked(True)
        dn = fn.GetDisplayNode() # dn: Display Node
        dn.SetSelectedColor(0,1,0)
        dn.SetVisibility(True)


    def placeScanFiducialOnCreatedPlane(self,x,y,z,idx):
        fn = slicer.util.getNode("sf_" + str(idx))
        fn.AddFiducial(x,y,z)


class VelmexController:
    def __init__(self, controller = None):
        self.ser = None
        self.OnemmToStep = None
        self.Xpos = None
        self.Ypos = None
        self.Zpos = None
        self.waveform = None
        self.oldx, self.oldy, self.oldz = 0, 0, 0
        self.newx, self.newy, self.newz = 0, 0, 0

    def Setup(self):
        # initialization and open the port
        # possible timeout values:
        #    1. None: wait forever, block call
        #    2. 0: non-blocking mode, return immediately
        #    3. x, x is bigger than 0, float allowed, timeout block call
        self.ser = serial.Serial()
        # Serial port must be set your USB port / --> ex : "/dev/ttyS2"
        self.ser.port = os.environ.get("VXM_SERIAL_PORT", "COM4")
        self.ser.baudrate = 9600
        self.ser.bytesize = serial.EIGHTBITS  # number of bits per bytes
        self.ser.parity = serial.PARITY_NONE  # set parity check: no parity
        self.ser.stopbits = serial.STOPBITS_ONE  # number of stop bits
        # ser.timeout = None          #block read
        self.ser.timeout = 100  # non-block read
        # ser.timeout = 2              #timeout block read
        self.ser.xonxoff = False  # disable software flow control
        self.ser.rtscts = False  # disable hardware (RTS/CTS) flow control
        self.ser.dsrdtr = False  # disable hardware (DSR/DTR) flow control
        self.ser.writeTimeout = 2  # timeout for write
        osc.setup()

        try:
            self.ser.open()

        except Exception as e:
            print("error open serial port: " + str(e))

            exit()

        if self.ser.isOpen():

            try:
                self.ser.flushInput()  # flush input buffer, discarding all its contents
                self.ser.flushOutput()  # flush output buffer, aborting current output
                # and discard all that is in buffer

                # write data
                self.ser.write("F,C,S1M2000,R".encode())
                self.ser.write("F,C,S2M2000,R".encode())
                self.ser.write("F,C,S3M2000,R".encode())

                self.ser.write("F,C,IA1M-0,R".encode())
                self.ser.write("F,C,IA2M-0,R".encode())
                self.ser.write("F,C,IA3M-0,R".encode())

                time.sleep(0.1)  # give the serial port sometime to receive the data

                conv = 400 / 2.54
                self.OnemmToStep = int(np.fix(conv))

            except Exception as e1:
                print("error communicating...: " + str(e1))

        else:
            print("cannot open serial port ")

        self.waveform = osc.getData()

    def clear(self):
        self.ser.close()
        osc.clear()

    def setStepSize(self, step):
        stepsize = self.OnemmToStep * step
        return stepsize

    def sleeptime(self, stepsize):
        step = abs(stepsize / self.OnemmToStep)
        if step != 1.0:
            print(step)
        if step <= 1:
            return 0.3
        elif step <= 5:
            return 0.8
        elif step <= 10:
            return 1.3
        elif step <= 20:
            return 2.0
        elif step <= 30:
            return 3.0
        elif step <= 100:
            return 10.0
        elif step <= 400:
            return 15.0
        else:  # step > 30 : sleep error
            return -1

    def Nmove(self, stepsize, axisparam):
        send = "F,C,I{0}M{1},R".format(axisparam, stepsize)
        self.ser.write(send.encode())
        time.sleep(self.sleeptime(stepsize))

    def Pmove(self, stepsize, axisparam):
        send = "F,C,I{0}-M{1},R".format(axisparam, stepsize)
        self.ser.write(send.encode())
        time.sleep(self.sleeptime(stepsize))

    def setOneDXYZ(self, a, axisparam):
        if axisparam == 1:
            self.newx = self.oldx + a
        elif axisparam == 2:
            self.newy = self.oldy + a
        else:
            self.newz = self.oldz + a

        self.oldx = self.newx
        self.oldy = self.newy
        self.oldz = self.newz

    def setTwoDXYZ(self, a, b, axisparam):
        if axisparam == [1, 2]:
            self.newx = self.oldx + a
            self.newy = self.oldy + b
        elif axisparam == [2, 3]:
            self.newy = self.oldy + a
            self.newz = self.oldz + b
        else:
            self.newx = self.oldx + b
            self.newz = self.oldz + a

        self.oldx = self.newx
        self.oldy = self.newy
        self.oldz = self.newz

    def setThreeDXYZ(self, a, b, c):
        self.newx = self.oldx + a
        self.newy = self.oldy + b
        self.newz = self.oldz + c

        self.oldx = self.newx
        self.oldy = self.newy
        self.oldz = self.newz

    def resetXYZ(self):
        self.newx, self.newy, self.newz = 0, 0, 0
        self.oldx, self.oldy, self.oldz = 0, 0, 0

    """
    def TwoDScanCompared(self, plus, minus, axisparam):
        self.Xpos = self.OneDScan(plus[0], minus[0], axisparam[0])
        self.Ypos = self.OneDScan(plus[1], minus[1], axisparam[1])

        Xlength = plus[0] + minus[0] + 1
        Ylength = plus[1] + minus[1] + 1

        oldXpos = self.Xpos
        oldYpos = self.Ypos
        i = 1
        print("1 step Old X, Y : ", oldXpos, oldYpos)
        while True:
            i += 1
            self.Xpos = self.OneDScan(Xlength - oldXpos, oldXpos - 1, axisparam[0])
            print("Xpos{}: ".format(i), self.Xpos)
            if oldXpos == self.Xpos:
                print("Yes Old same New X: ", oldXpos, self.Xpos)
                break
            self.Ypos = self.OneDScan(Ylength - oldYpos, oldYpos - 1, axisparam[1])
            print("Ypos{}: ".format(i), self.Ypos)
            if oldYpos == self.Ypos:
                print("Yes Old same New Y: ", oldYpos, self.Ypos)
                break
            oldXpos = self.Xpos
            oldYpos = self.Ypos
            print("step{} Old X, Y : ".format(i), oldXpos, oldYpos)
        print("lengthX,Y: ", Xlength, Ylength)
        print("posX,Y: ", oldXpos, oldYpos)
    """

class VXMControllerLogic(ScriptedLoadableModuleLogic):
    """This class should implement all the actual
  computation done by your module.  The interface
  should be such that other python code can import
  this class and make use of the functionality without
  requiring an instance of the Widget.
  Uses ScriptedLoadableModuleLogic base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

    def __init__(self):
        """
    Called when the logic class is instantiated. Can be used for initializing member variables.
    """
        ScriptedLoadableModuleLogic.__init__(self)

    def setDefaultParameters(self, parameterNode):
        """
    Initialize parameter node with default settings.
    """

    def process(self, inputVolume, outputVolume, imageThreshold, invert=False, showResult=True):
        """
    Run the processing algorithm.
    Can be used without GUI widget.
    :param inputVolume: volume to be thresholded
    :param outputVolume: thresholding result
    :param imageThreshold: values above/below this threshold will be set to 0
    :param invert: if True then values above the threshold will be set to 0, otherwise values below are set to 0
    :param showResult: show output volume in slice viewers
    """

#
# VXMControllerTest
#
