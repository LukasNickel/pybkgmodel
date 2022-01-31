import os
import re
import numpy
import pandas
import uproot
import astropy.time
import astropy.units as u

from astropy.coordinates import SkyCoord, EarthLocation, AltAz


class EventSample:
    def __init__(
            self, 
            event_ra, event_dec, event_energy,
            pointing_ra, pointing_dec, pointing_az, pointing_zd,
            mjd
        ):
        self.__event_ra = event_ra
        self.__event_dec = event_dec
        self.__event_energy = event_energy
        self.__pointing_ra = pointing_ra
        self.__pointing_dec = pointing_dec
        self.__pointing_az = pointing_az
        self.__pointing_zd = pointing_zd
        self.__mjd = mjd
        
    @property
    def event_ra(self):
        return self.__event_ra
    
    @property
    def event_dec(self):
        return self.__event_dec
    
    @property
    def event_energy(self):
        return self.__event_energy
    
    @property
    def pointing_ra(self):
        return self.__pointing_ra
    
    @property
    def pointing_dec(self):
        return self.__pointing_dec
    
    @property
    def pointing_az(self):
        return self.__pointing_az
    
    @property
    def pointing_zd(self):
        return self.__pointing_zd
    
    @property
    def pointing_alt(self):
        return 90 * u.deg - self.pointing_zd
    
    @property
    def mjd(self):
        return self.__mjd


class EventFile:
    file_name = ''
    obs_id = None

    def __init__(self, file_name, cuts=None):
        pass

    def __repr__(self):
        print(
f"""{type(self).__name__} instance
    {'File name':.<20s}: {self.file_name}
    {'Obs ID':.<20s}: {self.obs_id}
    {'Alt range':.<20s}: [{self.pointing_alt.min():.1f}, {self.pointing_alt.max():.1f}]
    {'Az range':.<20s}: [{self.pointing_az.min():.1f}, {self.pointing_az.max():.1f}]
    {'MJD range':.<20s}: [{self.mjd.min():.3f}, {self.mjd.max():.3f}]
"""
        )

        return super().__repr__()

    @classmethod
    def load_events(cls, file_name, cuts):
        pass

    @property
    def event_ra(self):
        return self.events.event_ra

    @property
    def event_dec(self):
        return self.events.event_dec

    @property
    def event_energy(self):
        return self.events.event_energy

    @property
    def pointing_ra(self):
        return self.events.pointing_ra

    @property
    def pointing_dec(self):
        return self.events.pointing_dec

    @property
    def pointing_az(self):
        return self.events.pointing_az

    @property
    def pointing_alt(self):
        return self.events.pointing_alt

    @property
    def mjd(self):
        return self.events.mjd


class MagicEventFile(EventFile):
    def __init__(self, file_name, cuts=None):
        super().__init__(file_name, cuts)

        self.file_name = file_name
        self.obs_id = self.get_obs_id(file_name)
        self.events = self.load_events(file_name, cuts)

    @classmethod
    def get_obs_id(cls, file_name):
        parsed = re.findall('.*/\d+_(\d+)_\w_[0-9\w]+\-W[\d\.\+]+\.root', file_name)
        if parsed:
            obs_id = int(parsed[0])
        else:
            raise RuntimeError(f'Can not find observations ID in {file_name}')
        
        return obs_id

    @classmethod
    def load_events(cls, file_name, cuts):
        """
        This method loads events from the pre-defiled file and returns them as a dictionary.

        Parameters
        ----------
        file_name: str
            Name of the MAGIC SuperStar/Melibea file to use.

        Returns
        -------
        dict:
            A dictionary with the even properties: charge / arrival time data, trigger, direction etc.
        """

        event_data = dict()

        array_list = [
            'MTriggerPattern_1.fPrescaled',
            'MRawEvtHeader_1.fStereoEvtNumber',
            'MRawEvtHeader_1.fDAQEvtNumber',
            'MStereoParDisp.fDirectionRA',
            'MStereoParDisp.fDirectionDec',
            'MEnergyEst.fEnergy',
            'MPointingPos_1.fZd',
            'MPointingPos_1.fAz',
            'MPointingPos_1.fRa',
            'MPointingPos_1.fDec'
        ]

        data_units = {
            'event_ra': u.hourangle,
            'event_dec': u.deg,
            'event_energy': u.GeV,
            'pointing_ra':  u.hourangle,
            'pointing_dec': u.deg,
            'pointing_az': u.deg,
            'pointing_zd': u.deg,
            'mjd': u.d,
        }

        time_array_list = ['MTime_1.fMjd', 'MTime_1.fTime.fMilliSec', 'MTime_1.fNanoSec']

        mc_array_list = ['MMcEvt_1.fEnergy', 'MMcEvt_1.fTheta', 'MMcEvt_1.fPhi']

        data_names_mapping = {
            'MTriggerPattern_1.fPrescaled': 'trigger_pattern',
            'MRawEvtHeader_1.fStereoEvtNumber': 'stereo_event_number',
            'MRawEvtHeader_1.fDAQEvtNumber': 'daq_event_number',
            'MStereoParDisp.fDirectionRA': 'event_ra',
            'MStereoParDisp.fDirectionDec': 'event_dec',
            'MEnergyEst.fEnergy': 'event_energy',
            'MPointingPos_1.fZd': 'pointing_zd',
            'MPointingPos_1.fAz': 'pointing_az',
            'MPointingPos_1.fRa': 'pointing_ra',
            'MPointingPos_1.fDec': 'pointing_dec',
        }

        mc_names_mapping = {
            'MMcEvt_1.fEnergy': 'true_energy',
            'MMcEvt_1.fTheta': 'true_zd',
            'MMcEvt_1.fPhi': 'true_az'
        }

        with uproot.open(file_name) as input_file:
            if 'Events' in input_file:
                data = input_file['Events'].arrays(array_list, cut=cuts, library="np")

                # Mapping the read structure to the alternative names
                for key in data:
                    name = data_names_mapping[key]
                    event_data[name] = data[key]

                is_mc = 'MMcEvt_1.' in input_file['Events']
                if is_mc:
                    data = input_file['Events'].arrays(mc_array_list, cut=cuts, library="np")

                    # Mapping the read structure to the alternative names
                    for key in data:
                        name = mc_names_mapping[key]
                        event_data[name] = data[key]

                    # Post processing
                    event_data['true_zd'] = numpy.degrees(event_data['true_zd'])
                    event_data['true_az'] = numpy.degrees(event_data['true_az'])
                    # Transformation from Monte Carlo to usual azimuth
                    event_data['true_az'] = -1 * (event_data['true_az'] - 180 + 7)
                else:
                    # Reading the event arrival time information
                    data = input_file['Events'].arrays(time_array_list, cut=cuts, library="np")

                    # Computing the event arrival time
                    mjd = data['MTime_1.fMjd']
                    millisec = data['MTime_1.fTime.fMilliSec']
                    nanosec = data['MTime_1.fNanoSec']

                    event_data['mjd'] = mjd + (millisec / 1e3 + nanosec / 1e9) / 86400.0

            else:
                # The file is likely corrupted, so return empty arrays
                for key in data_names_mapping:
                    name = data_names_mapping[key]
                    event_data[name] = numpy.zeros(0)
                    
        finite = [numpy.isfinite(event_data[key]) for key in event_data]
        all_finite = numpy.prod(finite, axis=0, dtype=bool)
        
        for key in event_data:
            event_data[key] = event_data[key][all_finite]

            if key in data_units:
                event_data[key] = event_data[key] * data_units[key]

        event_sample = EventSample(
            event_data['event_ra'],
            event_data['event_dec'],
            event_data['event_energy'],
            event_data['pointing_ra'],
            event_data['pointing_dec'],
            event_data['pointing_az'],
            event_data['pointing_zd'],
            event_data['mjd']
        )

        return event_sample


class LstEventFile:
    def __init__(self, file_name, cuts=None):
        self.file_name = file_name
        
        self.events = self.load_events(file_name, cuts)
    
    @property
    def event_ra(self):
        #return self.events['reco_ra'].values * u.deg
        return self.events['RA'].values * u.deg
    
    @property
    def event_dec(self):
        #return self.events['reco_dec'].values * u.deg
        return self.events['DEC'].values * u.deg
    
    @property
    def event_energy(self):
        return self.events['reco_energy'].values * u.TeV
    
    @property
    def pointing_ra(self):
        lst_time = astropy.time.Time(self.mjd, format='mjd')
        lst_loc = EarthLocation(lat=28.761758*u.deg, lon=-17.890659*u.deg, height=2200*u.m)
        alt_az_frame = AltAz(obstime=lst_time, location=lst_loc)
        
        lst_altaz = SkyCoord(self.pointing_az, self.pointing_alt, frame=alt_az_frame)

        return lst_altaz.icrs.ra
    
    @property
    def pointing_dec(self):
        lst_time = astropy.time.Time(self.mjd, format='mjd')
        lst_loc = EarthLocation(lat=28.761758*u.deg, lon=-17.890659*u.deg, height=2200*u.m)
        alt_az_frame = AltAz(obstime=lst_time, location=lst_loc)
        
        lst_altaz = SkyCoord(self.pointing_az, self.pointing_alt, frame=alt_az_frame)
        
        return lst_altaz.icrs.dec
    
    @property
    def pointing_az(self):
        return self.events['az_tel'].values * u.rad
    
    @property
    def pointing_zd(self):
        return 90 * u.deg - self.pointing_alt
    
    @property
    def pointing_alt(self):
        return self.events['alt_tel'].values * u.rad
    
    @property
    def mjd(self):
        return astropy.time.Time(self.events['dragon_time'].values, format='unix').mjd

    @classmethod
    def load_events(cls, file_name, cuts):
        """
        This method loads events from the pre-defiled file and returns them as a dictionary.

        Parameters
        ----------
        file_name: str
            Name of the MAGIC SuperStar/Melibea file to use.

        Returns
        -------
        dict:
            A dictionary with the even properties: charge / arrival time data, trigger, direction etc.
        """

        event_data = pandas.read_hdf(
            file_name,
            key='dl2/event/telescope/parameters/LST_LSTCam'
        )
        if cuts:
            event_data = event_data.query(cuts)

        return event_data


class RunSummary:
    __obs_id = None
    __file_name = None
    __tel_pointing_start = None
    __tel_pointing_stop = None

    def __init__(self, file_name):
        _, ext = os.path.splitext(file_name)

        if ext.lower() == ".root":
            events = MagicEventFile(file_name)
        elif ext.lower() == ".h5":
            events = LstEventFile(file_name, cuts='')
        else:
            raise RuntimeError(f"Unknown file format '{ext}'. Supported are '.root' and '.h5'.")
    
        evt_selection = [events.mjd.argmin(), events.mjd.argmax()]
        time = astropy.time.Time(events.mjd[evt_selection], format='mjd')
        # TODO: make location configurable.
        lst_loc = EarthLocation(lat=28.761758*u.deg, lon=-17.890659*u.deg, height=2200*u.m)
        alt_az_frame = AltAz(obstime=time, location=lst_loc)
        
        pstart, pstop = SkyCoord(events.pointing_az[evt_selection], events.pointing_alt[evt_selection], frame=alt_az_frame)

        self.__file_name = file_name
        self.__obs_id = events.obs_id
        self.__tel_pointing_start = pstart
        self.__tel_pointing_stop = pstop
    
    def __repr__(self):
        print(
f"""{type(self).__name__} instance
    {'Data file':.<20s}: {self.file_name}
    {'Obs ID':.<20s}: {self.obs_id}
    {'MJD start':.<20s}: {self.mjd_start}
    {'MJD stop':.<20s}: {self.mjd_stop}
    {'Duration':.<20s}: {self.obs_duration}
    {'Pointing':.<20s}: {self.tel_pointing_start.icrs}
"""
        )

        return super().__repr__()

    @property
    def obs_id(self):
        return self.__obs_id

    @property
    def file_name(self):
        return self.__file_name

    @property
    def obs_duration(self):
        duration = (self.mjd_stop - self.mjd_start) * u.day
        return duration.to('s')

    @property
    def mjd_start(self):
        return self.tel_pointing_start.frame.obstime.mjd

    @property
    def mjd_stop(self):
        return self.tel_pointing_stop.frame.obstime.mjd

    @property
    def tel_pointing_start(self):
        return self.__tel_pointing_start

    @property
    def tel_pointing_stop(self):
        return self.__tel_pointing_stop

    def to_qtable(self):
        data = {
            'obs_id': [self.obs_id],
            'mjd_start': [self.mjd_start],
            'mjd_stop': [self.mjd_stop],
            'duration': [self.obs_duration],
            'az_tel_start': [self.tel_pointing_start.az.to('deg')],
            'az_tel_stop': [self.tel_pointing_stop.az.to('deg')],
            'alt_tel_start': [self.tel_pointing_start.alt.to('deg')],
            'alt_tel_stop': [self.tel_pointing_stop.alt.to('deg')],
            'file_name': [self.file_name]
        }

        return astropy.table.QTable(data)
