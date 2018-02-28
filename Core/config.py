# -*- coding: utf-8 -*-
"""
@author: migalin
@contact: https://migalin.ru
@license Apache License, Version 2.0, see LICENSE file
Copyright (C) 2018
"""

from .CoreClasses import VKAnalysisLoader, VKAnalysisInfo

VKAnalysisInfo['version'] = 180224
VKAnalysisInfo['version_status'] = 'alpha'

# MODULE VKTextAnalisys
from VKTextAnalisys.TextAnalysisWidget import VKTextAnalysisWidget
VKAnalysisLoader['text'] = VKTextAnalysisWidget
# END VKTextAnalisys

# MODULE VKPhotoAnalysis
from VKPhotoAnalysis.PhotoAnalysisWidgets import PhotoAnalysisWidget
VKAnalysisLoader['photo'] = PhotoAnalysisWidget
# END VKPhotoAnalysis

# MODULE VKActivityAnalisys
from VKActivityAnalisys import FriendsActivityAnalysisWidget, \
    InterestingActivityAnalysisWidget#, TimeActivityAnalysisWidget
#VKAnalysisLoader['online'] = TimeActivityAnalysisWidget
VKAnalysisLoader['interest'] = InterestingActivityAnalysisWidget
VKAnalysisLoader['circle'] = FriendsActivityAnalysisWidget
# END VKActivityAnalisys
