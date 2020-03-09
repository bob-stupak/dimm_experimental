# common_parms.py
#
# This module contains all of the common variable for the DIMM package
#
import platform
import sys
import os
import os.path
#
# Basic information for the DIMM site
#
DIMLAT=+31.957827    #Mountain
DIMLNG=-111.597893   #Mountain
DIMELV=2072.0        #Mountain
#DIMLAT=+31.957778    #Mountain
#DIMLNG=-111.598056   #Mountain
#DIMELV=2072.0        #Mountain
#DIMLAT=+32.233060     #NOAO Tucson Parking lot
#DIMLNG=-110.947108    #NOAO Tucson Parking lot
#DIMELV=746.3
#DIMLAT=+32.243822    #HMELAT
#DIMLNG=-110.798858   #HMELNG
#DIMELV=778.0         #HMEELV
SITE_UTC_OFFSET=7.0
# Use for time.strftime(DTIME_FORMAT).split(',') to get current date/time
DTIME_FORMAT='%m/%d/%Y,%H:%M:%S'
#
# The base path for the DIMM package
#
#DIMM_HOST='140.252.5.166'
DIMM_HOST='140.252.57.2' #'140.252.57.2/24' on eno2
DIMM_PRIV='169.254.95.1' #'169.254.95.1/16' on eno1
if platform.uname()[1]=='dimm-1u':
  DIMM_DIR='/home/mpg/experimental/'
elif 'rstupak' in os.path.abspath('./'):
  DIMM_DIR='/home/rstupak/bin/pyDir/dimm/src/experimental/'
else:
  DIMM_DIR='./experimental/'
#
# The following parameters are the logging file and times
#
LOG_DIR=DIMM_DIR+'logs/'
MNG_LOGBASENAME='manager.log'
CAM_LOGBASENAME='camera.log'
SRC_LOGBASENAME='sources.log'
TELE_LOGBASENAME='telescope.log'
IMG_LOGBASENAME='imgprocess.log'
#
#TCP definitions 
#
#Telescope
TELE_SOCK_HOST='169.254.95.100'
TELE_SOCK_PORT=966
#Dome
DOME_SOCK_HOST='169.254.95.102'
DOME_SOCK_PORT=966
#
#Serial port definitions
#
#Telescope
if platform.system()=='Linux':
  TELE_SER_PORT='/dev/ttyUSB0'
else:
  TELE_SER_PORT='/dev/cu.usbserial-A7032WWB'
TELE_SER_BAUD=9600
TELE_SER_PARITY=None
TELE_SER_BITS=8
TELE_SER_FLOW=None
TELE_SER_START=1
TELE_SER_STOP=1
#Dome
DOME_SER_PORT_LINUX='/dev/ttyUSB0'
DOME_SER_PORT_MACOS='/dev/cu.usbserial-A7032WWB'
DOME_SER_BAUD=9600
DOME_SER_PARITY=None
DOME_SER_BITS=8
DOME_SER_FLOW=None
DOME_SER_STOP=1
#
# The following are Manager thread specific constants
#
MNG_THREAD_TIME=0.1
#
#  The following are Dome specific constants
#
DOME_THREADTIME=0.3  #Dome thread loop sleeptime
#
# The following definitions are used mostly for the source_cat_thread.py module
#
#CAT_NAME='bsc5.edb'
CAT_NAME='dimm.edb'
CAT_DIR=DIMM_DIR+'catalogs/'

MAG_LIMIT=3.0    #Magnitude selection limit
MAG_LIMIT_MAX=-18.0    #Maximum Magnitude selection limit
ZEN_LIMIT=50.0   #Zenith distance selection limit
ZEN_MINIMUM=5.0 #Minimum zenith distance

PLANETS=['Moon','Mercury','Venus','Mars','Jupiter','Saturn','Uranus',\
         'Neptune','Pluto']

SRC_THREAD_TIME=0.1  #Source process thread loop sleeptime
SRC_UPDATE_TIME=10000  #Number of milliseconds to update catalog
#
# The following definitions are used mostly for the telescope_thread.py module
#
TELE_THREAD_TIME=0.2  #Telescope thread loop sleeptime
#TELE_LOG_TIME=100   # Log time in milli seconds
#TELE_LOG_TIME=50   # Log time in milli seconds
TELE_LOG_TIME=10   # Log time in milli seconds
#
# The following parameters are the Meade LX200GPS 10" physical parameters along
#     with the sub-aperture parameters
TELE_NAME='Meade LX-200'
TELE_DIAM=0.2540            #[m] Telescope full diameter
TELE_FLENGTH=2500.0
TELE_FRATIO=10.0           #Focal-Ratio
TELE_SUBAPERTURE=0.0946    #[m] sub-aperture diameter
TELE_SUBSEPARATION=0.1497  #[m] sub-aperture separation
TELE_SUBSPREAD=40.0        #[arcsec] angular sub-aperture separation
TELE_FSPEED=(0,+2.0)       #[pixel/sec] focus motor speed
# Can use >>>eval('TELE_PARK_POS'+str(i))  to choose park position
TELE_PARK_POS1=['359*59\'10','+00*00\'00']
TELE_PARK_POS2=['090*00\'00','+00*00\'00']
TELE_PARK_POS3=['000*00\'50','+32*14\'50']
#
TELE_SPEEDS=[2,2,1,1]
  #Are the four preset telescope rates [tracking,slew,guide,center]
#TELE_TOLERANCE=0.01
TELE_TOLERANCE=0.075
  #The position tolerance for the on-source event, in degrees
TELE_SLEW_SPEEDS=['600x','900x','1200x']
  #Command <RSi> where i is 0= 600x, 1= 900x, 2= 1200x
TELE_CENTER_SPEEDS=['12x','64x','600x','1200x']
  #Command <RCi> where i is 0= 12x, 1= 64x, 2= 600x, 3=1200x
TELE_GUIDE_SPEEDS=['0.25x','0.5x','1.0x']
  #Command <RGi> where i is 0= 0.25x, 1= 0.5x, 2= 1.0x
TELE_TRACK_SPEEDS=['Lunar','Solar','Sidereal','Stop']
  #Command <RTi> where i is 0=Lunar, 1=Solar, 2=Sidereal, 9=Stop Tracking
TELE_FOCUS_SPEEDS=['Slow','Fast']
  #Command <Fi> where i is '-'=Slow and '+'=Fast
#
# The following definitions are the image_proc_thread.py common constants
#
IMG_PRC_THREADTIME=0.1  #Image processing thread loop sleeptime
IMG_DIR=DIMM_DIR+'imgdata/'
IMG_LIST=os.listdir(IMG_DIR)
#
#FINDER_XCENTER=164   # May 2018
#FINDER_YCENTER=132   # May 2018
#FINDER_XCENTER=180   # 5 Aug 2018
#FINDER_YCENTER=100   # 5 Aug 2018
#FINDER_XCENTER=168   # 1 Nov 2018
#FINDER_YCENTER=114   # 1 Nov 2018
#FINDER_XCENTER=188   # 4 Apr 2019
#FINDER_YCENTER=113   # 4 Apr 2019
FINDER_XCENTER=154   # 5 Nov 2019
FINDER_YCENTER=125   # 5 Nov 2019
####
#FINDER_XCENTER=1280/2
#FINDER_YCENTER=960/2
FND_CTR_MV_TIME=1.5 #Time to wait while telescope is searching, used in centering image to finder/image center coords
FND_CTR_MV_DIST=20  #The number of pixels away from a defined center to stop centering routine
FND_CTR_MV_ITER=15   #The number of iterations to run in order to center an image
CAM_CTR_MV_TIME=2.0 #Time to wait while telescope is searching, used in centering image to finder/image center coords
CAM_CTR_MV_DIST=35  #The number of pixels away from a defined center to stop centering routine
CAM_CTR_MV_ITER=15   #The number of iterations to run in order to center an image
SEEING_NUMBER=200     #The number of measurement to be taken for an individual seeing measurement
#SEEING_NUMBER=20     #The number of measurement to be taken for an individual seeing measurement
DIMM_MEAS_PER_SRC=20  #The number of seeing measurements per source
#DIMM_MEAS_PER_SRC=5  #The number of seeing measurements per source
SIM_IMAGE_NAME='test_m41_2.0sec.fits'
FOCUS_MOVE_TIME=1.0 #Time to wait while telescope is moving the focus, used in focusing image
FOCUS_MOVE_ITER=5   #The number of iterations to run in order to focus an image
#
# A list of available cameras
#
CAMERA_LIST=['file','Simulation','GT1290','GX2750','SBIG','Video']
#
# The following definitions are the camera specific constants
#
CAM_THREAD_TIME=0.1  #Camera thread loop sleeptime
#CAM_LOG_TIME=100   # Log time in milli seconds
#CAM_LOG_TIME=50   # Log time in milli seconds
CAM_LOG_TIME=10   # Log time in milli seconds
#The following are the initial exposure sequence times for a camera.
#
#SEQ_EXPTIMES can be used to set-up a repeated sequence of exposure times.
####SEQ_EXPTIMES=[0.01] #Sequenced exposure time list in seconds
####SEQ_DELAY=0.2     #The delay in seconds between exposures in the auto_sequencing of exposures
####SEQ_TOTAL_NUM=100000000  #The total number of sequences to be taken in auto_sequencing, default 100000000 'indefinite'
#
# The video channel for using a usb video camera
#
VIDEO_CHANNEL=1
#VIDEO_CHANNEL=0
#
# The following parameters are the camera specifications
#
#The GENERIC camera parameters for simulation
CAMERA_NAME='Simulation'      #Camera Generic
CAMERA_DEVICENAME='simulation'
#CAMERA_X=2750               #Total number of pixels in the x axis
#CAMERA_Y=2200               #Total number of pixels in the y axis
CAMERA_X=1280
CAMERA_Y=960
#CAMERA_X=765               #Total number of pixels in the x axis
#CAMERA_Y=510               #Total number of pixels in the y axis
CAMERA_PIXSIZE=4.54         #Pixel size in microns
CAMERA_X_PIXSIZE=4.54       #Pixel size in microns
CAMERA_Y_PIXSIZE=4.54       #Pixel size in microns
CAMERA_X_BINNING=1         #Binning in the horizontal direction
CAMERA_Y_BINNING=1         #Binning in the vertical direction
CAMERA_BIT=8               #Camera A/D
CAMERA_SAT_LEV=2**CAMERA_BIT       #Saturation level
CAMERA_EXP_TIME=0.1        #Camera exposure time, for single exposure
CAMERA_GAIN=0              #Camera gain
CAMERA_SEQ_EXPTIMES=[0.01] #Sequenced exposure time list in seconds
CAMERA_SEQ_DELAY=0.2     #The delay in seconds between exposures in the auto_sequencing of exposures
CAMERA_SEQ_TOTAL_NUM=100000000  #The total number of sequences to be taken in auto_sequencing, default 100000000 'indefinite'

#The SBIG ST-7 camera parameters
CAMERA_SBIG_NAME='ST-7XMEI'     #Camera SBIG model ST-7XMEI
CAMERA_SBIG_DEVICENAME='serial'
CAMERA_SBIG_X=765               #Total number of pixels in the x axis
CAMERA_SBIG_Y=510               #Total number of pixels in the y axis
CAMERA_SBIG_PIXSIZE=9.0         #Pixel size in microns
CAMERA_SBIG_X_PIXSIZE=9.0       #Pixel size in microns
CAMERA_SBIG_Y_PIXSIZE=9.0       #Pixel size in microns
CAMERA_SBIG_X_BINNING=1
CAMERA_SBIG_Y_BINNING=1
CAMERA_SBIG_BIT=16              #Camera A/D
CAMERA_SBIG_SAT_LEV=2**CAMERA_SBIG_BIT       #Saturation level
CAMERA_SBIG_EXP_TIME=0.1        #Camera exposure time, for single exposure
CAMERA_SBIG_GAIN=2.3            #Camera gain
#CAMERA_SBIG_NOISE=15.0          #Noise
#CAMERA_SBIG_CFZM=2.0e8          ###with 10" aperture
#CAMERA_SBIG_TEMP_CCD=0.0        #CCD temperature
CAMERA_SBIG_SEQ_EXPTIMES=[0.01] #Sequenced exposure time list in seconds
CAMERA_SBIG_SEQ_DELAY=0.2     #The delay in seconds between exposures in the auto_sequencing of exposures
CAMERA_SBIG_SEQ_TOTAL_NUM=100000000  #The total number of sequences to be taken in auto_sequencing, default 100000000 'indefinite'

#The Prosilica GX2750 camera parameters
CAMERA_GX2750_NAME='GX2750'
CAMERA_GX2750_DEVICENAME='DEV_000F31021BE2'
CAMERA_GX2750_X=2752
CAMERA_GX2750_Y=2200
CAMERA_GX2750_PIXSIZE=4.54
CAMERA_GX2750_X_PIXSIZE=4.54
CAMERA_GX2750_Y_PIXSIZE=4.54
CAMERA_GX2750_X_BINNING=1
CAMERA_GX2750_Y_BINNING=1
CAMERA_GX2750_BIT=14               #Camera A/D
CAMERA_GX2750_SAT_LEV=2**CAMERA_GX2750_BIT
CAMERA_GX2750_EXP_TIME=0.1         #Exposure time in usec
CAMERA_GX2750_GAIN=0               #Gain in dB
CAMERA_GX2750_SEQ_EXPTIMES=[0.1]  #Sequenced exposure time list in seconds
CAMERA_GX2750_SEQ_DELAY=0.2     #The delay in seconds between exposures in the auto_sequencing of exposures
CAMERA_GX2750_SEQ_TOTAL_NUM=100000000  #The total number of sequences to be taken in auto_sequencing, default 100000000 'indefinite'

#The Prosilica GT1290 camera parameters
CAMERA_GT1290_NAME='GT1290'
CAMERA_GT1290_DEVICENAME='DEV_000F31030804'
CAMERA_GT1290_X=1280
CAMERA_GT1290_Y=960
CAMERA_GT1290_PIXSIZE=3.75
CAMERA_GT1290_X_PIXSIZE=3.75
CAMERA_GT1290_Y_PIXSIZE=3.75
CAMERA_GT1290_X_BINNING=1
CAMERA_GT1290_Y_BINNING=1
CAMERA_GT1290_BIT=14
CAMERA_GT1290_SAT_LEV=2**CAMERA_GT1290_BIT
CAMERA_GT1290_EXP_TIME=0.1
CAMERA_GT1290_GAIN=0
CAMERA_GT1290_SEQ_EXPTIMES=[0.1] #Sequenced exposure time list in seconds
CAMERA_GT1290_SEQ_DELAY=0.2     #The delay in seconds between exposures in the auto_sequencing of exposures
CAMERA_GT1290_SEQ_TOTAL_NUM=100000000  #The total number of sequences to be taken in auto_sequencing, default 100000000 'indefinite'

#The SuperCircuits camera parameters
CAMERA_PC164C_NAME='PC164C'           #Camera SuperCircuits model PC164C, Sony ICX254AL chip
CAMERA_PC164C_DEVICENAME='1'
CAMERA_PC164C_X=320                   #Total number of pixels in the x axis
CAMERA_PC164C_Y=240                   #Total number of pixels in the y axis
CAMERA_PC164C_PIXSIZE=8.55            #Average Pixel size in microns
CAMERA_PC164C_X_PIXSIZE=9.6           #Pixel size in microns
CAMERA_PC164C_Y_PIXSIZE=7.5           #Pixel size in microns
CAMERA_PC164C_X_BINNING=1
CAMERA_PC164C_Y_BINNING=1
CAMERA_PC164C_BIT=8                   #Camera A/D
CAMERA_PC164C_SAT_LEV=2**CAMERA_PC164C_BIT #Saturation level
CAMERA_PC164C_EXP_TIME=0.0            #Camera exposure time, for single exposure
CAMERA_PC164C_GAIN=1.0                #Camera gain
#CAMERA_PC164C_NOISE=0.0               #Noise
#CAMERA_PC164C_CFZM=1.0e0              #
#CAMERA_PC164C_TEMP_CCD=0.0            #CCD temperature
CAMERA_PC164C_SEQ_EXPTIMES=[0.01] #Sequenced exposure time list in seconds
CAMERA_PC164C_SEQ_DELAY=0.2     #The delay in seconds between exposures in the auto_sequencing of exposures
CAMERA_PC164C_SEQ_TOTAL_NUM=100000000  #The total number of sequences to be taken in auto_sequencing, default 100000000 'indefinite'
