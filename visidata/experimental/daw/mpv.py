import os
import os.path
import socket
import json
import time
import subprocess
import shlex

from visidata import AttrDict, Sheet, vd


vd.option('daw_mpv_cmd', '/usr/bin/mpv --no-terminal --ao=pulse', '')


class MpvProcess:
    mpvproc = None

    afilters = dict(
        agate=[AttrDict(key=k, desc=desc) for k, desc in dict(
            level_in='input level before filtering',
            mode='upward=higher parts amplified; downward=lower parts reduced',
            range='level of gain reduction when the signal is below the threshold',
            threshold='If a signal rises above this level the gain reduction is released',
            ratio='ratio by which the signal is reduced',
            attack='milliseconds the signal has to rise above the threshold before gain reduction stops',
            release='milliseconds the signal has to fall below the threshold before the reduction is increased again',
            makeup='amount of amplification of signal after processing',
            knee='Curve the sharp knee around the threshold to enter gain reduction more softly',
            detection='if exact signal should be taken for detection or an RMS like one',
            link='if the average level between all channels or the louder channel affects the reduction'
         ).items()],
        loudnorm=[AttrDict(key=k, desc=desc) for k, desc in dict(
           i='integrated loudness target',
           lra='loudness range target',
           tp='maximum true peak',
           measured_i='Measured IL of input file',
           measured_lra='Measured LRA of input file',
           measured_tp='Measured true peak of input file',
           measured_thresh='Measured threshold of input file',
           offset='offset gain. Gain is applied before the true-peak limiter',
           linear='Normalize by linearly scaling the source audio',
           dual_mono='Treat mono input files as "dual-mono"',
         ).items()])
    # possible values across buttons 0 (default) to 9
    afilter_options = dict(agate=dict(
                                level_in=[1, 0.015625, 0.03, 0.1, 0.3, 1, 3, 10, 30, 64],
                                mode=['downward', 'upward'],
                                range=[0.06125,.1,.2,.3,.4,.5,.6,.7,.8,.9],
                                threshold=[0.125,.1,.2,.3,.4,.5,.6,.7,.8,.9],
                                ratio=[2,1,3,10,30,100,300,1000,3000,9000],
                                attack=[20, 0.01, .1, 1, 3, 10, 30, 100, 1000, 9000],
                                release=[250, 0.01, .1, 1, 3, 10, 30, 100, 1000, 9000],
                                makeup=[1,1,2,3,4,6,8,16,32,64],
                                knee=[2.828427,1,2,2.8,3,4,5,6,7,8],
                                detection=['rms', 'peak'],
                                link=['average', 'maximum']),
                           loudnorm=dict(
                               i=[-24.0],
                               lra=[7.0],
                               tp=[-0.0],
                               measured_i=[None],
                               measured_lra=[None],
                               measured_tp=[None],
                               measured_thresh=[None],
                               offset=[0, -99,-50,-20,-5,5,20,50,99],
                               linear=[True, False],
                               dual_mono=[False, True],
                           ))
    afilter_parms = {}

    def __init__(self, sourcefn, source:Sheet):
        self.sourceaudio = sourcefn
        self.mpvproc = None
        self.source = source

    def add_filter(self, filtername):
        self.afilter_parms[filtername] = {
            parmname:values[0] for parmname, values in self.afilter_options[filtername].items()
        }
        vd.status(f'filter {filtername} added')

    def remove_filter(self, filtername):
        del self.afilter_parms[filtername]

    def set_filter_parm(self, filtername, parmname, val):
        if filtername not in self.afilter_parms:
            self.add_filter(filtername)
        self.afilter_parms[filtername][parmname] = val
        self.restart_mpv(self.source.cursorRow.start) # self.playback_time

    @property
    def mpvsockfn(self):
        return '/tmp/vdmpv'

    def restart_mpv(self, t:float):
        self.start_mpv()
        time.sleep(0.5)
        self.seek_audio(t, 'absolute')
        self.pause_audio(False)

    def is_default(self, filtername, parmname, val):
        return val is None or val == self.afilter_options[filtername][parmname][0]

    def start_mpv(self):
        if self.mpvproc:
            self.mpv_command(command=["quit"])
            self.mpvproc = None

        if os.path.exists(self.mpvsockfn):
            os.unlink(self.mpvsockfn)

        if not os.path.exists(self.mpvsockfn):
            if not os.path.exists(self.sourceaudio):
                vd.warning(f'{self.sourceaudio} does not exist')
                return

            filterparams = ','.join(
                    (f'{filtername}=' + ':'.join(f'{k}={v}' for k, v in filterparms.items() if not self.is_default(filtername, k, v)))
                        for filtername, filterparms in self.afilter_parms.items())

            if filterparams:
                filterparams = '--af='+filterparams
                vd.status(filterparams)

            cmd = shlex.split(vd.options.daw_mpv_cmd)
            cmd.append(f'--input-ipc-server={self.mpvsockfn}')
            cmd.append(filterparams)
            cmd.append(self.sourceaudio)
            self.mpvproc = vd.popen(cmd)

    def mpv_command(self, **kwargs):
        sock = socket.socket(socket.AF_UNIX)
        sock.connect(self.mpvsockfn)
        sock.sendall(json.dumps(kwargs).encode() + b'\n')
        sock.close()

    def mpv_query(self, propname):
        sock = socket.socket(socket.AF_UNIX)
        try:
            sock.connect(self.mpvsockfn)
            sock.sendall(json.dumps(dict(command=['get_property', propname])).encode() + b'\n')
            r = sock.recv(4096)
            for line in r.splitlines():
                d = json.loads(line)
                error = d.get('error', '')
                if error != 'success':
                    vd.error(f"mpv error ({propname}): {error}")
            return d['data']
        except FileNotFoundError as e:
            vd.warning(str(e))
        finally:
            sock.close()

    def set_property(self, propname, b=True):
        self.mpv_command(command=['set_property', propname, b])

    @property
    def paused(self):
        p = self.mpv_query('pause')
#        vd.status(f'paused={p}')
        return p

    @property
    def playback_time(self):
        t = self.mpv_query('playback-time')
        if t is not None:
            return float(t)

    def pause_audio(self, b=True):
        self.set_property('pause', b)

    def play_audio(self, t:float):
        self.seek_audio(t, 'absolute')
        self.pause_audio(False)

    def seek_audio(self, dt:float, *args):
        self.mpv_command(command=['seek', str(dt), *args])
