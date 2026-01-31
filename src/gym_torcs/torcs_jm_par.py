import socket
import sys
import getopt
import os
import time
PI= 3.14159265359

data_size = 2**17

ophelp=  'Options:\n'
ophelp+= ' --host, -H <host>    TORCS server host. [localhost]\n'
ophelp+= ' --port, -p <port>    TORCS port. [3001]\n'
ophelp+= ' --id, -i <id>        ID for server. [SCR]\n'
ophelp+= ' --steps, -m <#>      Maximum simulation steps. 1 sec ~ 50 steps. [100000]\n'
ophelp+= ' --episodes, -e <#>   Maximum learning episodes. [1]\n'
ophelp+= ' --track, -t <track>  Your name for this track. Used for learning. [unknown]\n'
ophelp+= ' --stage, -s <#>      0=warm up, 1=qualifying, 2=race, 3=unknown. [3]\n'
ophelp+= ' --debug, -d          Output full telemetry.\n'
ophelp+= ' --help, -h           Show this help.\n'
ophelp+= ' --version, -v        Show current version.'
usage= 'Usage: %s [ophelp [optargs]] \n' % sys.argv[0]
usage= usage + ophelp
version= "20130505-2"

def clip(v,lo,hi):
    if v<lo: return lo
    elif v>hi: return hi
    else: return v

def bargraph(x,mn,mx,w,c='X'):
    '''Draws a simple asciiart bar graph. Very handy for
    visualizing what's going on with the data.
    x= Value from sensor, mn= minimum plottable value,
    mx= maximum plottable value, w= width of plot in chars,
    c= the character to plot with.'''
    if not w: return '' # No width!
    if x<mn: x= mn      # Clip to bounds.
    if x>mx: x= mx      # Clip to bounds.
    tx= mx-mn # Total real units possible to show on graph.
    if tx<=0: return 'backwards' # Stupid bounds.
    upw= tx/float(w) # X Units per output char width.
    if upw<=0: return 'what?' # Don't let this happen.
    negpu, pospu, negnonpu, posnonpu= 0,0,0,0
    if mn < 0: # Then there is a negative part to graph.
        if x < 0: # And the plot is on the negative side.
            negpu= -x + min(0,mx)
            negnonpu= -mn + x
        else: # Plot is on pos. Neg side is empty.
            negnonpu= -mn + min(0,mx) # But still show some empty neg.
    if mx > 0: # There is a positive part to the graph
        if x > 0: # And the plot is on the positive side.
            pospu= x - max(0,mn)
            posnonpu= mx - x
        else: # Plot is on neg. Pos side is empty.
            posnonpu= mx - max(0,mn) # But still show some empty pos.
    nnc= int(negnonpu/upw)*'-'
    npc= int(negpu/upw)*c
    ppc= int(pospu/upw)*c
    pnc= int(posnonpu/upw)*'_'
    return '[%s]' % (nnc+npc+ppc+pnc)

class Client():
    def __init__(self,H=None,p=None,i=None,e=None,t=None,s=None,d=None,vision=False):
        self.vision = vision

        self.host= 'localhost'
        self.port= 3001
        self.sid= 'SCR'
        self.maxEpisodes=1 # "Maximum number of learning episodes to perform"
        self.trackname= 'unknown'
        self.stage= 3 # 0=Warm-up, 1=Qualifying 2=Race, 3=unknown <Default=3>
        self.debug= False
        self.maxSteps= 100000  # 50steps/second
        self.parse_the_command_line()
        if H: self.host= H
        if p: self.port= p
        if i: self.sid= i
        if e: self.maxEpisodes= e
        if t: self.trackname= t
        if s: self.stage= s
        if d: self.debug= d
        self.S= ServerState()
        self.R= DriverAction()
        self.setup_connection()

    def setup_connection(self):
        try:
            self.so= socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        except socket.error as emsg:
            print('Error: Could not create socket...')
            sys.exit(-1)
        self.so.settimeout(1)

        n_fail = 5
        while True:
            a= "-45 -19 -12 -7 -4 -2.5 -1.7 -1 -.5 0 .5 1 1.7 2.5 4 7 12 19 45"

            initmsg='%s(init %s)' % (self.sid,a)

            try:
                self.so.sendto(initmsg.encode(), (self.host, self.port))
            except socket.error as emsg:
                sys.exit(-1)
            sockdata= str()
            try:
                sockdata,addr= self.so.recvfrom(data_size)
                sockdata = sockdata.decode('utf-8')
            except socket.error as emsg:
                print("Waiting for server on %d............" % self.port)
                print("Count Down : " + str(n_fail))
                if n_fail < 0:
                    print("relaunch torcs")
                    os.system('pkill torcs')
                    time.sleep(1.0)
                    if self.vision is False:
                        os.system('torcs -nofuel -nodamage -nolaptime &')
                    else:
                        os.system('torcs -nofuel -nodamage -nolaptime -vision &')

                    time.sleep(1.0)
                    os.system('sh autostart.sh')
                    n_fail = 5
                n_fail -= 1

            identify = '***identified***'
            if identify in sockdata:
                print("Client connected on %d.............." % self.port)
                break

    def parse_the_command_line(self):
        try:
            (opts, args) = getopt.getopt(sys.argv[1:], 'H:p:i:m:e:t:s:dhv',
                       ['host=','port=','id=','steps=',
                        'episodes=','track=','stage=',
                        'debug','help','version'])
        except getopt.error as why:
            print('getopt error: %s\n%s' % (why, usage))
            sys.exit(-1)
        try:
            for opt in opts:
                if opt[0] == '-h' or opt[0] == '--help':
                    print(usage)
                    sys.exit(0)
                if opt[0] == '-d' or opt[0] == '--debug':
                    self.debug= True
                if opt[0] == '-H' or opt[0] == '--host':
                    self.host= opt[1]
                if opt[0] == '-i' or opt[0] == '--id':
                    self.sid= opt[1]
                if opt[0] == '-t' or opt[0] == '--track':
                    self.trackname= opt[1]
                if opt[0] == '-s' or opt[0] == '--stage':
                    self.stage= int(opt[1])
                if opt[0] == '-p' or opt[0] == '--port':
                    self.port= int(opt[1])
                if opt[0] == '-e' or opt[0] == '--episodes':
                    self.maxEpisodes= int(opt[1])
                if opt[0] == '-m' or opt[0] == '--steps':
                    self.maxSteps= int(opt[1])
                if opt[0] == '-v' or opt[0] == '--version':
                    print('%s %s' % (sys.argv[0], version))
                    sys.exit(0)
        except ValueError as why:
            print('Bad parameter \'%s\' for option %s: %s\n%s' % (
                                       opt[1], opt[0], why, usage))
            sys.exit(-1)
        if len(args) > 0:
            print('Superflous input? %s\n%s' % (', '.join(args), usage))
            sys.exit(-1)

    def get_servers_input(self):
        '''Server's input is stored in a ServerState object'''
        if not self.so: return
        sockdata= str()

        while True:
            try:
                sockdata,addr= self.so.recvfrom(data_size)
                sockdata = sockdata.decode('utf-8')
            except socket.error as emsg:
                print('.', end=' ')
            if '***identified***' in sockdata:
                print("Client connected on %d.............." % self.port)
                continue
            elif '***shutdown***' in sockdata:
                print((("Server has stopped the race on %d. "+
                        "You were in %d place.") %
                        (self.port,self.S.d['racePos'])))
                self.shutdown()
                return
            elif '***restart***' in sockdata:
                print("Server has restarted the race on %d." % self.port)
                self.shutdown()
                return
            elif not sockdata: # Empty?
                continue       # Try again.
            else:
                self.S.parse_server_str(sockdata)
                if self.debug:
                    sys.stderr.write("\x1b[2J\x1b[H") # Clear for steady output.
                    print(self.S)
                break # Can now return from this function.

    def respond_to_server(self):
        if not self.so: return
        try:
            message = repr(self.R)
            self.so.sendto(message.encode(), (self.host, self.port))
        except socket.error as emsg:
            print("Error sending to server: %s Message %s" % (emsg[1],str(emsg[0])))
            sys.exit(-1)
        if self.debug: print(self.R.fancyout())

    def shutdown(self):
        if not self.so: return
        print(("Race terminated or %d steps elapsed. Shutting down %d."
               % (self.maxSteps,self.port)))
        self.so.close()
        self.so = None

class ServerState():
    '''What the server is reporting right now.'''
    def __init__(self):
        self.servstr= str()
        self.d= dict()

    def parse_server_str(self, server_string):
        '''Parse the server string.'''
        self.servstr= server_string.strip()[:-1]
        sslisted= self.servstr.strip().lstrip('(').rstrip(')').split(')(')
        for i in sslisted:
            w= i.split(' ')
            self.d[w[0]]= destringify(w[1:])

    def __repr__(self):
        return self.fancyout()
        out= str()
        for k in sorted(self.d):
            strout= str(self.d[k])
            if type(self.d[k]) is list:
                strlist= [str(i) for i in self.d[k]]
                strout= ', '.join(strlist)
            out+= "%s: %s\n" % (k,strout)
        return out

    def fancyout(self):
        '''Specialty output for useful ServerState monitoring.'''
        out= str()
        sensors= [ # Select the ones you want in the order you want them.
        'stucktimer',
        'fuel',
        'distRaced',
        'distFromStart',
        'opponents',
        'wheelSpinVel',
        'z',
        'speedZ',
        'speedY',
        'speedX',
        'targetSpeed',
        'rpm',
        'skid',
        'slip',
        'track',
        'trackPos',
        'angle',
        ]

        for k in sensors:
            if type(self.d.get(k)) is list: # Handle list type data.
                if k == 'track': # Nice display for track sensors.
                    strout= str()
                    raw_tsens= ['%.1f'%x for x in self.d['track']]
                    strout+= ' '.join(raw_tsens[:9])+'_'+raw_tsens[9]+'_'+' '.join(raw_tsens[10:])
                elif k == 'opponents': # Nice display for opponent sensors.
                    strout= str()
                    for osensor in self.d['opponents']:
                        if   osensor >190: oc= '_'
                        elif osensor > 90: oc= '.'
                        elif osensor > 39: oc= chr(int(osensor/2)+97-19)
                        elif osensor > 13: oc= chr(int(osensor)+65-13)
                        elif osensor >  3: oc= chr(int(osensor)+48-3)
                        else: oc= '?'
                        strout+= oc
                    strout= ' -> '+strout[:18] + ' ' + strout[18:]+' <-'
                else:
                    strlist= [str(i) for i in self.d[k]]
                    strout= ', '.join(strlist)
            else: # Not a list type of value.
                if k == 'gear': # This is redundant now since it's part of RPM.
                    gs= '_._._._._._._._._'
                    p= int(self.d['gear']) * 2 + 2  # Position
                    l= '%d'%self.d['gear'] # Label
                    if l=='-1': l= 'R'
                    if l=='0':  l= 'N'
                    strout= gs[:p]+ '(%s)'%l + gs[p+3:]
                elif k == 'damage':
                    strout= '%6.0f %s' % (self.d[k], bargraph(self.d[k],0,10000,50,'~'))
                elif k == 'fuel':
                    strout= '%6.0f %s' % (self.d[k], bargraph(self.d[k],0,100,50,'f'))
                elif k == 'speedX':
                    cx= 'X'
                    if self.d[k]<0: cx= 'R'
                    strout= '%6.1f %s' % (self.d[k], bargraph(self.d[k],-30,300,50,cx))
                elif k == 'speedY': # This gets reversed for display to make sense.
                    strout= '%6.1f %s' % (self.d[k], bargraph(self.d[k]*-1,-25,25,50,'Y'))
                elif k == 'speedZ':
                    strout= '%6.1f %s' % (self.d[k], bargraph(self.d[k],-13,13,50,'Z'))
                elif k == 'z':
                    strout= '%6.3f %s' % (self.d[k], bargraph(self.d[k],.3,.5,50,'z'))
                elif k == 'trackPos': # This gets reversed for display to make sense.
                    cx='<'
                    if self.d[k]<0: cx= '>'
                    strout= '%6.3f %s' % (self.d[k], bargraph(self.d[k]*-1,-1,1,50,cx))
                elif k == 'stucktimer':
                    if self.d[k]:
                        strout= '%3d %s' % (self.d[k], bargraph(self.d[k],0,300,50,"'"))
                    else: strout= 'Not stuck!'
                elif k == 'rpm':
                    g= self.d['gear']
                    if g < 0:
                        g= 'R'
                    else:
                        g= '%1d'% g
                    strout= bargraph(self.d[k],0,10000,50,g)
                elif k == 'angle':
                    asyms= [
                          "  !  ", ".|'  ", "./'  ", "_.-  ", ".--  ", "..-  ",
                          "---  ", ".__  ", "-._  ", "'-.  ", "'\.  ", "'|.  ",
                          "  |  ", "  .|'", "  ./'", "  .-'", "  _.-", "  __.",
                          "  ---", "  --.", "  -._", "  -..", "  '\.", "  '|."  ]
                    rad= self.d[k]
                    deg= int(rad*180/PI)
                    symno= int(.5+ (rad+PI) / (PI/12) )
                    symno= symno % (len(asyms)-1)
                    strout= '%5.2f %3d (%s)' % (rad,deg,asyms[symno])
                elif k == 'skid': # A sensible interpretation of wheel spin.
                    frontwheelradpersec= self.d['wheelSpinVel'][0]
                    skid= 0
                    if frontwheelradpersec:
                        skid= .5555555555*self.d['speedX']/frontwheelradpersec - .66124
                    strout= bargraph(skid,-.05,.4,50,'*')
                elif k == 'slip': # A sensible interpretation of wheel spin.
                    frontwheelradpersec= self.d['wheelSpinVel'][0]
                    slip= 0
                    if frontwheelradpersec:
                        slip= ((self.d['wheelSpinVel'][2]+self.d['wheelSpinVel'][3]) -
                              (self.d['wheelSpinVel'][0]+self.d['wheelSpinVel'][1]))
                    strout= bargraph(slip,-5,150,50,'@')
                else:
                    strout= str(self.d[k])
            out+= "%s: %s\n" % (k,strout)
        return out

class DriverAction():
    '''What the driver is intending to do (i.e. send to the server).
    Composes something like this for the server:
    (accel 1)(brake 0)(gear 1)(steer 0)(clutch 0)(focus 0)(meta 0) or
    (accel 1)(brake 0)(gear 1)(steer 0)(clutch 0)(focus -90 -45 0 45 90)(meta 0)'''
    def __init__(self):
       self.actionstr= str()
       self.d= { 'accel':0.2,
                   'brake':0,
                  'clutch':0,
                    'gear':1,
                   'steer':0,
                   'focus':[-90,-45,0,45,90],
                    'meta':0
                    }

    def clip_to_limits(self):
        """There pretty much is never a reason to send the server
        something like (steer 9483.323). This comes up all the time
        and it's probably just more sensible to always clip it than to
        worry about when to. The "clip" command is still a snakeoil
        utility function, but it should be used only for non standard
        things or non obvious limits (limit the steering to the left,
        for example). For normal limits, simply don't worry about it."""
        self.d['steer']= clip(self.d['steer'], -1, 1)
        self.d['brake']= clip(self.d['brake'], 0, 1)
        self.d['accel']= clip(self.d['accel'], 0, 1)
        self.d['clutch']= clip(self.d['clutch'], 0, 1)
        if self.d['gear'] not in [-1, 0, 1, 2, 3, 4, 5, 6, 7]:
            self.d['gear']= 0
        if self.d['meta'] not in [0,1]:
            self.d['meta']= 0
        if type(self.d['focus']) is not list or min(self.d['focus'])<-180 or max(self.d['focus'])>180:
            self.d['focus']= 0

    def __repr__(self):
        self.clip_to_limits()
        out= str()
        for k in self.d:
            out+= '('+k+' '
            v= self.d[k]
            if not type(v) is list:
                out+= '%.3f' % v
            else:
                out+= ' '.join([str(x) for x in v])
            out+= ')'
        return out
        return out+'\n'

    def fancyout(self):
        '''Specialty output for useful monitoring of bot's effectors.'''
        out= str()
        od= self.d.copy()
        od.pop('gear','') # Not interesting.
        od.pop('meta','') # Not interesting.
        od.pop('focus','') # Not interesting. Yet.
        for k in sorted(od):
            if k == 'clutch' or k == 'brake' or k == 'accel':
                strout=''
                strout= '%6.3f %s' % (od[k], bargraph(od[k],0,1,50,k[0].upper()))
            elif k == 'steer': # Reverse the graph to make sense.
                strout= '%6.3f %s' % (od[k], bargraph(od[k]*-1,-1,1,50,'S'))
            else:
                strout= str(od[k])
            out+= "%s: %s\n" % (k,strout)
        return out

def destringify(s):
    '''makes a string into a value or a list of strings into a list of
    values (if possible)'''
    if not s: return s
    if type(s) is str:
        try:
            return float(s)
        except ValueError:
            print("Could not find a value in %s" % s)
            return s
    elif type(s) is list:
        if len(s) < 2:
            return destringify(s[0])
        else:
            return [destringify(i) for i in s]

def drive_example(c):
    '''This is only an example. It will get around the track but the
    correct thing to do is write your own `drive()` function.'''
    S,R= c.S.d,c.R.d
    target_speed=160

    R['steer']= S['angle']*25 / PI
    R['steer']-= S['trackPos']*.25

    R['accel'] = max(0.0, min(1.0, R['accel']))
    

    if S['speedX'] < target_speed - (R['steer']*2.5):
        R['accel']+= .4
    else:
        R['accel']-= .2
    if S['speedX']<10:
       R['accel']+= 1/(S['speedX']+.1)

    if ((S['wheelSpinVel'][2]+S['wheelSpinVel'][3]) -
       (S['wheelSpinVel'][0]+S['wheelSpinVel'][1]) > 2):
       R['accel']-= 0.1



    R['gear']=1
    if S['speedX']>60:
        R['gear']=2
    if S['speedX']>100:
        R['gear']=3
    if S['speedX']>140:
        R['gear']=4
    if S['speedX']>190:
        R['gear']=5
    if S['speedX']>220:
        R['gear']=6
    return

# NOTE: The drive_example function above is just a basic example.
# The improved drive_modular function below is what actually runs!
# See the main loop at the bottom of this file.



#############################################
# MODULAR DRIVE LOGIC WITH USER PARAMETERS  #
#############################################

import math

# ================= OPTIMIZED PARAMETERS FOR CORKSCREW =================
# These parameters are tuned for the Laguna Seca track, specifically handling
# the tricky Corkscrew section and high-speed cornering.

# Speed targets
TARGET_SPEED = 300      # Maximum speed on straights (F1 capable)
MIN_TARGET_SPEED = 45   # Absolute minimum for hairpins to prevent stalling

# Steering dynamics
STEER_GAIN = 18.5       # Increased for sharper response in tight corners
SPEED_STEER_GAIN = 0.0018  # Reduces steering sensitivity at high speeds (stability)
CENTERING_GAIN = 0.28   # Force (gain) pulling the car back to the track center

# Speed penalties (reduced for more aggressive driving)
# These reduce target speed based on car state to safely navigate corners
ANGLE_PENALTY = 38.0    # Penalty for high angle relative to track axis
STEER_PENALTY = 32.0    # Penalty when steering heavily (avoids understeer)
TRACKPOS_PENALTY = 22.0 # Penalty for being off-center

# Lookahead bonuses
LOOKAHEAD_GAIN = 2.8    # Increases target speed if the road ahead is straight
EDGE_LIMIT = 0.92       # Distance from center (0-1) allowed before safety interventions

# Braking parameters (trail braking capable)
BRAKE_THRESHOLD = 2.5   # Speed delta above target before brakes engage
BRAKE_INTENSITY = 0.055 # How hard to brake per unit of overspeed
MAX_BRAKE = 1.0         # Maximum allowable brake pressure (ABS limit)
TRAIL_BRAKE_FACTOR = 0.35 # Retain some braking while turning (trail braking)

# Gear shift points optimized for F1
GEAR_UP_RPM = 18200     # Shift up near redline for max power
GEAR_DOWN_RPM = 8200    # Shift down to keep revs high and use engine braking

# Traction control (refined)
TC_ENABLED = True
TC_SLIP_THRESHOLD = 3.5 # Allowable difference between front/rear wheel speeds
TC_REDUCTION = 0.35     # Throttle multiplier when slip is detected

# Corner-specific targets (km/h) - Corkscrew optimized
# Heuristic-based speed limits for recognizable sections of Laguna Seca
TURN1_SPEED = 110       # Turn 1 entry
ANDRETTI_HAIRPIN = 72   # Turn 2 apex (tightest corner)
TURN3_SPEED = 135       # Turn 3 (uphill left)
TURN4_SPEED = 145       # Turn 4 (continuing uphill)
TURN5_SPEED = 118       # Turn 5 (downhill right)
TURN6_SPEED = 155       # Turn 6 (fast left before Corkscrew)
CORKSCREW_ENTRY = 95    # Turn 8 entry (Blind crest, iconic drop)
CORKSCREW_EXIT = 65     # Turn 8a exit (Compression)
RAINEY_CURVE = 165      # Turn 9 (downhill sweeper)
TURN10_SPEED = 138      # Turn 10 (right after Rainey)
TURN11_SPEED = 75       # Turn 11 (final hairpin before front straight)

# ================= ADVANCED HELPER FUNCTIONS =================

def calculate_steering(S):
    """
    Calculates the steering angle based on track position, angle, and curvature.
    
    Args:
        S (dict): Server state dictionary containing sensors like 'angle', 'trackPos', 'track'.
    
    Returns:
        float: Steering value between -1.0 (right) and 1.0 (left).
    """
    track = S['track']
    speed = max(1.0, S['speedX'])
    
    # 1. Dynamic steering gain: Lower gain at high speeds prevents oscillation
    base_gain = STEER_GAIN / (1.0 + SPEED_STEER_GAIN * speed)
    
    # 2. Base steering: Align with track axis and center the car
    # 'angle' is the angle between car direction and track axis
    # 'trackPos' is the distance from track center (-1 to 1)
    steer = (S['angle'] * base_gain / math.pi) - (S['trackPos'] * CENTERING_GAIN)
    
    # 3. Predictive steering: Look ahead using track edge sensors
    # Compare left vs right side open distance to anticipate curves
    if len(track) >= 19:
        left_sensor = track[0:5]    # Far left sensors
        right_sensor = track[14:19] # Far right sensors
        left_avg = sum(left_sensor) / len(left_sensor)
        right_avg = sum(right_sensor) / len(right_sensor)
        
        # Steer toward the side with more space (the "open" side)
        sensor_diff = (left_avg - right_avg) * 0.008
        steer += sensor_diff
    
    return max(-1.0, min(1.0, steer))

def identify_corner(S, min_ahead, speedZ, distFromStart):
    """
    Identifies the current track section on Laguna Seca based on distance and telemetry.
    This allows for tailored speed targets for specific difficult corners.
    
    Args:
        S (dict): Server state.
        min_ahead (float): Minimum distance seen by forward sensors.
        speedZ (float): Vertical speed (useful for detecting hills/drops).
        distFromStart (float): Total distance raced.
        
    Returns:
        tuple: (Corner Name, Target Speed)
    """
    # Normalize distance to lap length (Laguna Seca is approx 3600m)
    dist = distFromStart % 3610
    
    # Turn 1 (0-250m): Medium-fast right over a crest
    if 0 <= dist < 250 and min_ahead < 80:
        return ('TURN1', TURN1_SPEED)
    
    # Andretti Hairpin T2 (250-450m): Slowest, double-apex hair
    if 250 <= dist < 450 and min_ahead < 25:
        return ('ANDRETTI', ANDRETTI_HAIRPIN)
    
    # Turn 3 (450-800m): Uphill left
    if 450 <= dist < 800 and min_ahead < 50:
        return ('TURN3', TURN3_SPEED)
    
    # Turn 4 (800-1100m): Continuing uphill
    if 800 <= dist < 1100 and min_ahead < 60:
        return ('TURN4', TURN4_SPEED)
    
    # Turn 5 (1100-1400m): Downhill right, banked
    if 1100 <= dist < 1400 and speedZ < -0.3:
        return ('TURN5', TURN5_SPEED)
    
    # Turn 6 (1400-1700m): Fast left before the hill
    if 1400 <= dist < 1700 and min_ahead < 70:
        return ('TURN6', TURN6_SPEED)
    
    # Corkscrew (1700-2000m): The famous blind drop (Turn 8/8a)
    # Detects the drop using negative vertical speed (speedZ)
    if 1700 <= dist < 2000 and speedZ < -0.5:
        if min_ahead < 50:
            return ('CORKSCREW', CORKSCREW_ENTRY)
        else:
            return ('CORKSCREW_EXIT', CORKSCREW_EXIT)
    
    # Rainey Curve T9 (2000-2400m): Fast downhill sweeper
    if 2000 <= dist < 2400 and speedZ < -0.25 and min_ahead > 60:
        return ('RAINEY', RAINEY_CURVE)
    
    # Turn 10 (2400-2700m): Medium right
    if 2400 <= dist < 2700 and min_ahead < 55:
        return ('TURN10', TURN10_SPEED)
    
    # Turn 11 (2700-3100m): Final hairpin, crucial for start/finish speed
    if 2700 <= dist < 3100 and min_ahead < 28:
        return ('TURN11', TURN11_SPEED)
    
    # Default: Straightaway logic
    return ('STRAIGHT', TARGET_SPEED)

def calculate_target_speed(S, R, min_ahead, avg_ahead):
    """
    Determines the optimal speed for the current situation.
    Combines track lookahead with specific corner knowledge.
    """
    speedZ = S.get('speedZ', 0)
    distFromStart = S.get('distFromStart', 0)
    
    # 1. Identify specific corner to get hardcoded limit
    _, corner_target = identify_corner(S, min_ahead, speedZ, distFromStart)
    
    # 2. Calculate dynamic limit based on visibility (lookahead)
    # The further we see, the faster we can go.
    base = MIN_TARGET_SPEED + LOOKAHEAD_GAIN * avg_ahead
    base = min(TARGET_SPEED, max(MIN_TARGET_SPEED, base))
    
    # 3. Apply the strictest limit (corner-specific vs dynamic)
    base = min(base, corner_target)
    
    # 4. Apply dynamic penalties based on stability state
    base -= abs(S['angle']) * ANGLE_PENALTY       # Slow down if car is sideways
    base -= abs(R['steer']) * STEER_PENALTY       # Slow down if steering hard
    base -= abs(S['trackPos']) * TRACKPOS_PENALTY # Slow down if near edges
    
    # 5. Critical Edge Safety: Drastic slowdown if about to go off-track
    if abs(S['trackPos']) > EDGE_LIMIT:
        base -= 35.0
    
    return max(MIN_TARGET_SPEED, base)

def calculate_throttle(S, R, target_speed):
    """
    Controls accelerator pedal trying to match target speed.
    """
    speed_diff = target_speed - S['speedX']
    speed = S['speedX']
    
    # 1. Progressive Throttle Map
    # Apply more throttle when far below target, feather it when close.
    if speed_diff > 20:
        accel = 1.0
    elif speed_diff > 10:
        accel = 0.85
    elif speed_diff > 5:
        accel = 0.65
    elif speed_diff > 0:
        accel = 0.40
    else:
        accel = 0.10  # Maintain momentum
    
    # 2. Launch Control
    # Full power at very low speeds to get moving
    if speed < 15:
        accel = max(accel, 0.95)
    
    # 3. Brake Interaction
    # Reduce throttle significantly if also braking (trail braking modulation)
    if R['brake'] > 0.5:
        accel *= 0.3
    elif R['brake'] > 0:
        accel *= 0.6
    
    return max(0.0, min(1.0, accel))

def apply_brakes(S, R, target_speed):
    """
    Manages braking logic, including trail braking and emergency stops.
    """
    speed = S['speedX']
    
    # Don't brake at crawling speeds
    if speed < 8:
        return 0.0
    
    # Calculate how much we are over our target speed
    over = speed - (target_speed + BRAKE_THRESHOLD)
    
    if over <= 0:
        # Trail Braking Logic: 
        # Even if not speeding, keep light brake pressure during sharp turns
        # to load front tires and help rotation.
        if abs(R['steer']) > 0.3 and speed > 60:
            return TRAIL_BRAKE_FACTOR * abs(R['steer'])
        return 0.0
    
    # Standard Braking: Proportional to overspeed
    brake = min(MAX_BRAKE, over * BRAKE_INTENSITY)
    
    # Emergency Braking: Panic stop if going off track
    if abs(S['trackPos']) > EDGE_LIMIT:
        brake = max(brake, 0.6)
    
    return brake

def shift_gears(S):
    """
    Automatic transmission logic.
    Prioritizes RPM for performance, with speed-based fallback.
    """
    gear = int(S.get('gear', 1))
    rpm = S.get('rpm', 0)
    speed = S['speedX']
    
    # Strategy 1: RPM-based shifting (Optimal)
    if rpm and gear > 0:
        if rpm > GEAR_UP_RPM and gear < 6:
            return gear + 1
        if rpm < GEAR_DOWN_RPM and gear > 1:
            return gear - 1
        return gear
    
    # Strategy 2: Speed-based shifting (Fallback if RPM sensor fails)
    if speed < 30:
        return 1
    if speed < 70:
        return 2
    if speed < 110:
        return 3
    if speed < 150:
        return 4
    if speed < 195:
        return 5
    return 6

def traction_control(S, accel):
    """
    Basic Traction Control System (TCS).
    Reduces throttle if rear wheels are spinning significantly faster than fronts.
    """
    if not TC_ENABLED:
        return accel
    
    # Compare average rear wheel speed vs average front wheel speed
    rear_speed = (S['wheelSpinVel'][2] + S['wheelSpinVel'][3]) / 2.0
    front_speed = (S['wheelSpinVel'][0] + S['wheelSpinVel'][1]) / 2.0
    wheel_slip = rear_speed - front_speed
    
    # Dynamic reduction based on severity of slip
    if wheel_slip > TC_SLIP_THRESHOLD * 2:
        accel *= 0.4  # Major cut for major slip
    elif wheel_slip > TC_SLIP_THRESHOLD:
        accel *= (1.0 - TC_REDUCTION)  # Moderate cut for minor slip
    
    return max(0.0, accel)

# ================= MAIN DRIVE FUNCTION =================

# State tracking globals
last_speeds = []
stuck_counter = 0
recovery_mode = False

def drive_optimized(c):
    """
    Optimized racing driver for Laguna Seca lap times.
    Integrates all modular components (steering, speed, gears) into a cohesive drive loop.
    Includes logic to detect getting stuck and recovering.
    """
    global last_speeds, stuck_counter, recovery_mode
    
    S, R = c.S.d, c.R.d
    
    # === STUCK DETECTION ===
    # Monitors variance in speed over the last 60 ticks.
    # If speed is low and not changing, we are likely stuck against a wall.
    last_speeds.append(S['speedX'])
    if len(last_speeds) > 60:
        last_speeds.pop(0)
        
        speed_var = max(last_speeds) - min(last_speeds)
        if speed_var < 0.3 and S['speedX'] < 8:
            stuck_counter += 1
        else:
            stuck_counter = 0
            recovery_mode = False
    
    # === STUCK RECOVERY BEHAVIOR ===
    # Reverse and turn to unstuck.
    if stuck_counter > 30 or recovery_mode:
        recovery_mode = True
        R['gear'] = -1      # Reverse gear
        R['accel'] = 0.8    # High throttle
        R['brake'] = 0.0
        # Wiggle steering
        R['steer'] = -0.6 if stuck_counter % 80 < 40 else 0.6
        
        # Reset after enough time
        if stuck_counter > 150:
            stuck_counter = 0
            recovery_mode = False
            last_speeds = []
        return
    
    # === SENSOR ANALYSIS ===
    track = S['track']
    
    # Extract key track sensors (center and near-center) to judge road straightness
    # Sensor index 9 is straight ahead. 0 is far left, 18 is far right.
    ahead_left = track[8] if len(track) > 8 else 200
    ahead_center = track[9] if len(track) > 9 else 200
    ahead_right = track[10] if len(track) > 10 else 200
    
    min_ahead = min(ahead_left, ahead_center, ahead_right)
    avg_ahead = (ahead_left + ahead_center + ahead_right) / 3.0
    
    # === EXECUTE CONTROL LOGIC ===
    R['steer'] = calculate_steering(S)
    target_speed = calculate_target_speed(S, R, min_ahead, avg_ahead)
    R['brake'] = apply_brakes(S, R, target_speed)
    R['accel'] = calculate_throttle(S, R, target_speed)
    R['accel'] = traction_control(S, R['accel'])
    R['gear'] = shift_gears(S)

# ================= MAIN LOOP =================
if __name__ == "__main__":
    print("=" * 60)
    print("LAGUNA SECA OPTIMIZED RACING AI")
    print("F1 Configuration - Maximum Attack Mode")
    print("=" * 60)
    C = Client(p=3001)
    for step in range(C.maxSteps, 0, -1):
        C.get_servers_input()
        drive_optimized(C)
        C.respond_to_server()
    C.shutdown()