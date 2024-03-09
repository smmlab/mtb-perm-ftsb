import sys
import os
import glob
from java.io import File

from ij import IJ
from ij import WindowManager

from fiji.plugin.trackmate import Model
from fiji.plugin.trackmate import Settings
from fiji.plugin.trackmate import TrackMate
from fiji.plugin.trackmate import SelectionModel
from fiji.plugin.trackmate import Logger
from fiji.plugin.trackmate.detection import DogDetectorFactory
from fiji.plugin.trackmate.tracking.jaqaman import SimpleSparseLAPTrackerFactory
from fiji.plugin.trackmate.gui.displaysettings import DisplaySettingsIO
import fiji.plugin.trackmate.visualization.hyperstack.HyperStackDisplayer as HyperStackDisplayer
import fiji.plugin.trackmate.features.FeatureFilter as FeatureFilter
from fiji.plugin.trackmate.io import TmXmlWriter
from fiji.plugin.trackmate.util import TMUtils
from fiji.plugin.trackmate.visualization.table import TrackTableView
from fiji.plugin.trackmate.visualization.table import AllSpotsTableView
from fiji.plugin.trackmate import SelectionModel
from fiji.plugin.trackmate.gui.displaysettings import DisplaySettings
import fiji.plugin.trackmate.action.ExportTracksToXML as ExportTracksToXML

# We have to do the following to avoid errors with UTF8 chars generated in 
# TrackMate that will mess with our Fiji Jython.
reload(sys)
sys.setdefaultencoding('utf-8')
 
# Get a directory
#@ File (label="Select a directory", style="directory") dir

def process_directory(image_directory):

	# Get list of image files in directory
	files = glob.glob(image_directory + 'PALM*.tif')
	
	i = 0
	N = len(files)
	
	# Process and save trackmate analysis for each PALM movie
	for f in files:
	
		print(' '.join(['Processing file',str(i+1),'of',str(N)]))
		i += 1
	
		imp = IJ.openImage(f)
		imp.show()
		
		# 100 nm pixels and 33 ms frame rate
		imp.getCalibration().setXUnit("nm");
		IJ.run(imp, "Properties...", "channels=1 slices=1 frames=2500 pixel_width=100 pixel_height=100 voxel_depth=100 frame=[33 ms]");
		
		model = Model()
		model.setLogger(Logger.IJ_LOGGER)
		
		settings = Settings(imp)
		 
		# Configure detector - We use the Strings for the keys
		settings.detectorFactory = DogDetectorFactory()
		settings.trackerSettings = settings.detectorFactory.getDefaultSettings() # almost good enough
		settings.detectorSettings = {
		    'DO_SUBPIXEL_LOCALIZATION' : True,
		    'RADIUS' : 2.5, #250.,
		    'TARGET_CHANNEL' : 1,
		    'THRESHOLD' : 160.,
		    'DO_MEDIAN_FILTERING' : True,
		}
		
		settings.trackerFactory = SimpleSparseLAPTrackerFactory()
		settings.trackerSettings = settings.trackerFactory.getDefaultSettings()
		settings.trackerSettings['GAP_CLOSING_MAX_DISTANCE'] = 500.
		settings.trackerSettings['LINKING_MAX_DISTANCE'] = 500.
		settings.trackerSettings['MAX_FRAME_GAP'] = 0
		
		settings.addAllAnalyzers()
		
		trackmate = TrackMate(model, settings)
		
		ok = trackmate.checkInput()
		if not ok:
		    sys.exit(str(trackmate.getErrorMessage()))
		 
		ok = trackmate.process()
		if not ok:
		    sys.exit(str(trackmate.getErrorMessage()))
		    
		selectionModel = SelectionModel( model )
		
		ds = DisplaySettingsIO.readUserDefault()
		 
		displayer =  HyperStackDisplayer( model, selectionModel, imp, ds )
		displayer.render()
		displayer.refresh()
		
		model.getLogger().log( str( model ) )
		
		# save trackmate file with default name in data folder
		saveFile = TMUtils.proposeTrackMateSaveFile( settings, Logger.IJ_LOGGER )
		writer = TmXmlWriter( saveFile, Logger.IJ_LOGGER )
		writer.appendLog( Logger.IJ_LOGGER.toString() )
		writer.appendModel( trackmate.getModel() )
		writer.appendSettings( trackmate.getSettings() )
		writer.writeToFile();
		
		# Export tracks only XML
		saveFile = File(f[:-4] + '_tracks.xml')
		ExportTracksToXML.export(trackmate.getModel(), trackmate.getSettings(), saveFile)
	
		imp.close()
		
	return 'Done!'

d = dir.getPath()
subdirectories = [os.path.join(d, o) for o in os.listdir(d) 
                    if os.path.isdir(os.path.join(d,o))]

for s in subdirectories:
	if s.split('/')[-1][1]=='_':
		print('Processing ' + s)
		# print(process_directory(s + '/')) # for 231004 before directories were renamed to be consistent
		print(process_directory(s + '/mEos3.2_PALM/')) # for other days


