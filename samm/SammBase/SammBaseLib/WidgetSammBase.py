"""
MIT License
Copyright (c) 2022 [Insert copyright holders]
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import slicer, qt, zmq
from SammBaseLib.WidgetSamm import SammWidgetBase
from slicer.util import VTKObservationMixin
from vtk.util.numpy_support import vtk_to_numpy

class SammBaseWidget(SammWidgetBase):

    def __init__(self, parent=None):

        super().__init__(parent)

    def setup(self):

        super().setup()
        # Connections

        # These connections ensure that we update parameter node when scene is closed
        self.addObserver(slicer.mrmlScene, slicer.mrmlScene.StartCloseEvent, self.onSceneStartClose)
        self.addObserver(slicer.mrmlScene, slicer.mrmlScene.EndCloseEvent, self.onSceneEndClose)

        # UI
        self.ui.pushComputePredictor.connect('clicked(bool)', self.onPushComputePredictor)
        self.ui.pushStartMaskSync.connect('clicked(bool)', self.onPushStartMaskSync)
        self.ui.comboVolumeNode.connect("currentNodeChanged(vtkMRMLNode*)", self.updateParameterNodeFromGUI)
        self.ui.markupsAdd.connect("markupsNodeChanged()", self.updateParameterNodeFromGUI)
        self.ui.markupsRemove.connect("markupsNodeChanged()", self.updateParameterNodeFromGUI)
        self.ui.markupsAdd.markupsPlaceWidget().setPlaceModePersistency(True)
        self.ui.markupsRemove.markupsPlaceWidget().setPlaceModePersistency(True)

        # Make sure parameter node is initialized (needed for module reload)
        self.initializeParameterNode()

        # Attach to logic
        self.logic.ui = self.ui

    def updateGUIFromParameterNode(self, caller=None, event=None):
        """
        This method is called whenever parameter node is changed.
        The module GUI is updated to show the current state of the parameter node.
        """

        if self._parameterNode is None or self._updatingGUIFromParameterNode:
            return

        # Make sure GUI changes do not call updateParameterNodeFromGUI (it could cause infinite loop)
        self._updatingGUIFromParameterNode = True

        # Update node selectors and sliders
        self.ui.comboVolumeNode.setCurrentNode(self._parameterNode.GetNodeReference("sammInputVolume"))
        self.ui.markupsAdd.setCurrentNode(self._parameterNode.GetNodeReference("sammPromptAdd"))
        self.ui.markupsRemove.setCurrentNode(self._parameterNode.GetNodeReference("sammPromptRemove"))
        
        # All the GUI updates are done
        self._updatingGUIFromParameterNode = False

    def updateParameterNodeFromGUI(self, caller=None, event=None):
        """
        This method is called when the user makes any change in the GUI.
        The changes are saved into the parameter node (so that they are restored when the scene is saved and loaded).
        """

        if self._parameterNode is None or self._updatingGUIFromParameterNode:
            return

        wasModified = self._parameterNode.StartModify()  # Modify all properties in a single batch

        self._parameterNode.SetNodeReferenceID("sammInputVolume", self.ui.comboVolumeNode.currentNodeID)
        self._parameterNode.SetNodeReferenceID("sammPromptAdd", self.ui.markupsAdd.currentNode().GetID())
        self._parameterNode.SetNodeReferenceID("sammPromptRemove", self.ui.markupsRemove.currentNode().GetID())

        self._parameterNode.EndModify(wasModified)

    def onPushComputePredictor(self):
        self.logic.processComputePredictor()

    def onPushStartMaskSync(self):
        self.logic.processStartPromptSync()
        self.logic._flag_prompt_sync = True
        self.logic.processStartMaskSync()
        self.logic._flag_mask_sync = True
