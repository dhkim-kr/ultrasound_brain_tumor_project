import os
import unittest
import logging
import vtk, qt, ctk, slicer

from slicer.ScriptedLoadableModule import *
from slicer.util import VTKObservationMixin
import numpy as np


#
# UpdateSlicePlane
#

class UpdateSlicePlane(ScriptedLoadableModule):
    """Uses ScriptedLoadableModule base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        self.parent.title = "UpdateSlicePlane"  # TODO: make this more human readable by adding spaces
        self.parent.categories = [
            "Mymodule"]  # TODO: set categories (folders where the module shows up in the module selector)
        self.parent.dependencies = []  # TODO: add here list of module names that this module requires
        self.parent.contributors = [
            "Daehyeon Kim (KIST & Kwangwoon Univ.)"]  # TODO: replace with "Firstname Lastname (Organization)"
        # TODO: update with short description of the module and a link to online module documentation
        self.parent.helpText = """
          This module provides the feature to move the slice planes to the coordinates of the stylusTip.
  """
        # TODO: replace with organization, grant and thanks
        self.parent.acknowledgementText = """
  """


#
# Register sample data sets in Sample Data module
#


#
# UpdateSlicePlaneWidget
#

class UpdateSlicePlaneWidget(ScriptedLoadableModuleWidget, VTKObservationMixin):
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
        self.Input1 = None
        self.Input2 = None
        self.InputNode1 = None
        self.InputNode2 = None
        # StylusTipToStylus node
        self.Tn_STTR = None
        self.TipsObservation = None
        # Auto-update mode : True
        self.ActiveStatus = False
        self.InitPos = []
        self.ResultPos = []
        self.applyButton = None
        self.autoButton = None
        self.stopButton = None
        self.resetButton = None

    def setup(self):
        """
    Called when the user opens the module the first time and the widget is initialized.
    """
        ScriptedLoadableModuleWidget.setup(self)

        # Set initial position of slice planes 'R', 'G', 'Y'
        InitPosR = slicer.app.layoutManager().sliceWidget('Red').mrmlSliceNode()
        InitPosG = slicer.app.layoutManager().sliceWidget('Green').mrmlSliceNode()
        InitPosY = slicer.app.layoutManager().sliceWidget('Yellow').mrmlSliceNode()

        # axis Z, Y, X value < - >  Plane XY, XZ, YZ
        self.InitPos = [InitPosR.GetSliceToRAS().GetElement(2, 3),
                        InitPosG.GetSliceToRAS().GetElement(1, 3),
                        InitPosY.GetSliceToRAS().GetElement(0, 3)]
        # -- initial position of slice planes setting done
        self.ResultPos = self.InitPos
        ##########################################################################################
        # Set input nodes
        ##########################################################################################
        InputTransforms = ctk.ctkCollapsibleButton()
        InputTransforms.text = "Input Transforms"
        self.layout.addWidget(InputTransforms)
        InputTransformsLayout = qt.QFormLayout(InputTransforms)
        
        self.Input1 = slicer.qMRMLNodeComboBox()
        self.Input1.nodeTypes = ["vtkMRMLLinearTransformNode"]
        self.Input1.selectNodeUponCreation = True
        self.Input1.addEnabled = False
        self.Input1.removeEnabled = False
        self.Input1.noneEnabled = False
        self.Input1.showHidden = False
        self.Input1.showChildNodeTypes = False
        self.Input1.setMRMLScene(slicer.mrmlScene)
        self.Input1.setToolTip("Pick the input transform.")
        InputTransformsLayout.addRow("Input Transform_1: ", self.Input1)

        self.Input2 = slicer.qMRMLNodeComboBox()
        self.Input2.nodeTypes = ["vtkMRMLLinearTransformNode"]
        self.Input2.selectNodeUponCreation = True
        self.Input2.addEnabled = False
        self.Input2.removeEnabled = False
        self.Input2.noneEnabled = False
        self.Input2.showHidden = False
        self.Input2.showChildNodeTypes = False
        self.Input2.setMRMLScene(slicer.mrmlScene)
        self.Input2.setToolTip("Pick the input transform.")
        InputTransformsLayout.addRow("Input Transform_2: ", self.Input2)

        ##########################################################################################
        # Set Buttons
        ##########################################################################################
        # Create buttons
        self.applyButton = qt.QPushButton("Apply")
        self.autoButton = qt.QPushButton("Auto")
        self.stopButton = qt.QPushButton("Stop")
        self.resetButton = qt.QPushButton("Reset")
        #  -- Create done

        # Set initial button properties
        self.applyButton.toolTip = "Update position of slice planes to current coordinate of StylusTip"
        self.applyButton.enabled = True
        self.autoButton.toolTip = "Update automatically"
        self.autoButton.enabled = True
        self.stopButton.toolTip = "It's not auto status"
        self.stopButton.enabled = False
        self.resetButton.toolTip = "It's already initial position"
        self.resetButton.enabled = False
        # -- Initial button properties setting done

        # Set layout
        Controller = ctk.ctkCollapsibleButton()
        Controller.text = "Slice Plane Controller"
        self.layout.addWidget(Controller)
        ControllerLayout = qt.QFormLayout(Controller)

        ControllerLayout.addRow(self.applyButton)
        ControllerLayout.addRow(self.autoButton)
        ControllerLayout.addRow(self.stopButton)
        ControllerLayout.addRow(self.resetButton)
        # -- Layout setting done

        # Set button trigger
        self.applyButton.connect('clicked(bool)', self.onApplyButton)
        self.autoButton.connect('clicked(bool)', self.onAutoButton)
        self.stopButton.connect('clicked(bool)', self.onStopButton)
        self.resetButton.connect('clicked(bool)', self.onResetButton)
        # -- Button trigger setting done
        """
        ##########################################################################################
        # Set result area
        ##########################################################################################
        result = ctk.ctkCollapsibleButton()
        result.text = "Result (Display Coordinate)"
        self.layout.addWidget(result)
        resultLayout = qt.QFormLayout(result)

        # Set ui
        self.labelname = qt.QLabel("Coordinate")
        self.labelname.setFixedWidth(100)
        resultLayout.addRow(self.labelname)

        self.XLabel = qt.QLabel("X")
        self.XLabel.setFixedWidth(10)
        self.XvalueBox = QLineEdit(self)
        self.XvalueBox.setReadOnly(True)
        self.XvalueBox.setText(str(self.InitPos[2]))
        self.XvalueBox.setTextMargins(-300, 15, 300, -15)
        #self.XvalueBox.value = self.InitPos[2]

        self.YLabel = qt.QLabel("Y")
        self.YLabel.setFixedWidth(10)
        self.YvalueBox = qt.QDoubleSpinBox()
        self.YvalueBox.setRange(-300, 300)
        self.YvalueBox.value = self.InitPos[1]

        self.ZLabel = qt.QLabel("Z")
        self.ZLabel.setFixedWidth(10)
        self.ZvalueBox = qt.QDoubleSpinBox()
        self.ZvalueBox.setRange(-300, 300)
        self.ZvalueBox.value = self.InitPos[0]

        PostionLayout = qt.QHBoxLayout()
        PostionLayout.addWidget(self.XLabel)
        PostionLayout.addWidget(self.XvalueBox)
        PostionLayout.addWidget(self.YLabel)
        PostionLayout.addWidget(self.YvalueBox)
        PostionLayout.addWidget(self.ZLabel)
        PostionLayout.addWidget(self.ZvalueBox)
        resultLayout.addRow(PostionLayout)
        """

    def cleanup(self):
        self.removeObservers()

    # Update plane from StylusTip
    def UpdateSlicePlane(self, Tn_STTR=None, Param2=None):
        self.InputNode2 = self.Input2.currentNode()
        # Transform matrix of StylusTipToReference and ReferenceToRas
        Tf_STTR = Tn_STTR.GetTransformToParent().GetMatrix()
        TM_STTR = np.zeros((4, 4), float)
        Tn_RTRs = self.InputNode2
        Tf_RTRs = Tn_RTRs.GetTransformToParent().GetMatrix()
        TM_RTRs = np.zeros((4, 4), float)
        # List to Numpy array (4 * 4 Matrix)
        for i in range(4):
            for j in range(4):
                TM_STTR[i][j] = Tf_STTR.GetElement(i, j)
                TM_RTRs[i][j] = Tf_RTRs.GetElement(i, j)
        # Set Translate matrix -->  StylusTipToRas : Real position of StylusTip and Real Position of slice views to
        # be moved
        TM = np.copy(np.dot(TM_RTRs, TM_STTR))
        Tl_M = TM[:3, 3]
        # get nodes
        SliceNode_R = slicer.app.layoutManager().sliceWidget('Red').mrmlSliceNode()
        SliceNode_G = slicer.app.layoutManager().sliceWidget('Green').mrmlSliceNode()
        SliceNode_Y = slicer.app.layoutManager().sliceWidget('Yellow').mrmlSliceNode()
        # update position
        SliceNode_R.GetSliceToRAS().SetElement(2, 3, Tl_M[2])
        SliceNode_G.GetSliceToRAS().SetElement(1, 3, Tl_M[1])
        SliceNode_Y.GetSliceToRAS().SetElement(0, 3, Tl_M[0])
        # Update all changes
        SliceNode_R.UpdateMatrices()
        SliceNode_G.UpdateMatrices()
        SliceNode_Y.UpdateMatrices()

        if not self.ActiveStatus:
            print("Coordinate - X: {}   Y: {}   Z: {}".format(Tl_M[0], Tl_M[1], Tl_M[2]))

    def ResetSlicePlane(self, param=None, param1=None, Param2=None):
        # get nodes
        SliceNode_R = slicer.app.layoutManager().sliceWidget('Red').mrmlSliceNode()
        SliceNode_G = slicer.app.layoutManager().sliceWidget('Green').mrmlSliceNode()
        SliceNode_Y = slicer.app.layoutManager().sliceWidget('Yellow').mrmlSliceNode()
        # reset position
        SliceNode_R.GetSliceToRAS().SetElement(2, 3, self.InitPos[0])
        SliceNode_G.GetSliceToRAS().SetElement(1, 3, self.InitPos[1])
        SliceNode_Y.GetSliceToRAS().SetElement(0, 3, self.InitPos[2])
        # Update all changes
        SliceNode_R.UpdateMatrices()
        SliceNode_G.UpdateMatrices()
        SliceNode_Y.UpdateMatrices()

        # InitPos: values of axis [Z, Y, X]  --  Descend order
        print("Coordinate - X: {}   Y: {}   Z: {}".format(self.InitPos[2], self.InitPos[1],
                                                          self.InitPos[0]))

    def onApplyButton(self):
        self.resetButton.toolTip = "Reset to initial position"
        self.resetButton.enabled = True

        self.InputNode1 = self.Input1.currentNode()
        self.Tn_STTR = self.InputNode1

        self.UpdateSlicePlane(self.Tn_STTR)

    def onAutoButton(self):
        self.ActiveStatus = True
        # Set button properties
        self.applyButton.toolTip = "It's auto-update status, click the Stop button"
        self.applyButton.enabled = False
        self.autoButton.toolTip = "It's already auto-update status"
        self.autoButton.enabled = False
        self.stopButton.toolTip = "Stop the auto-update"
        self.stopButton.enabled = True
        self.resetButton.toolTip = "It's auto-update status, click the Stop button"
        self.resetButton.enabled = False
        # -- Button properties setting done

        self.InputNode1 = self.Input1.currentNode()
        self.Tn_STTR = self.InputNode1
        self.TipsObservation = [self.Tn_STTR,
                                self.Tn_STTR.AddObserver(
                                    slicer.vtkMRMLTransformNode.TransformModifiedEvent, self.UpdateSlicePlane, 2)
                                ]

    def onStopButton(self):
        self.ActiveStatus = False
        # Set button properties
        self.applyButton.toolTip = "Update position of slice planes to current coordinate of StylusTip"
        self.applyButton.enabled = True
        self.autoButton.toolTip = "Update automatically"
        self.autoButton.enabled = True
        self.stopButton.toolTip = "It's not auto status"
        self.stopButton.enabled = False
        self.resetButton.toolTip = "Reset to initial position"
        self.resetButton.enabled = True
        # -- Button properties setting done

        self.TipsObservation[0].RemoveObserver(self.TipsObservation[1])
        self.InputNode1 = self.Input1.currentNode()
        self.Tn_STTR = self.InputNode1
        self.UpdateSlicePlane(self.Tn_STTR)

        self.TipsObservation = None

    def onResetButton(self):
        self.resetButton.toolTip = "It's already initial position"
        self.resetButton.enabled = False

        self.ResetSlicePlane()
        if self.TipsObservation is not None:
            self.TipsObservation[0].RemoveObserver(self.TipsObservation[1])


#
# UpdateSlicePlaneLogic
#
class UpdateSlicePlaneLogic(ScriptedLoadableModuleLogic):
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

    def process(self):
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
# UpdateSlicePlaneTest
#

class UpdateSlicePlaneTest(ScriptedLoadableModuleTest):
    """
  This is the test case for your scripted module.
  Uses ScriptedLoadableModuleTest base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

    def setUp(self):
        """ Do whatever is needed to reset the state - typically a scene clear will be enough.
    """
        slicer.mrmlScene.Clear()

    def runTest(self):
        """Run as few or as many tests as needed here.
    """
        self.setUp()
        self.test_UpdateSlicePlane1()

    def test_UpdateSlicePlane1(self):
        """ Ideally you should have several levels of tests.  At the lowest level
    tests should exercise the functionality of the logic with different inputs
    (both valid and invalid).  At higher levels your tests should emulate the
    way the user would interact with your code and confirm that it still works
    the way you intended.
    One of the most important features of the tests is that it should alert other
    developers when their changes will have an impact on the behavior of your
    module.  For example, if a developer removes a feature that you depend on,
    your test should break so they know that the feature is needed.
    """

        self.delayDisplay("Starting the test")

        # Get/create input data
