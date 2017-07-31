# -*- coding: utf-8 -*-

# Copyright or © or Copr. Thomas Duchesne <thomas@duchesne.io>, 2014-2015
# 
# This software was funded by the Van Allen Foundation <http://fondation-va.fr>.
# 
# This software is governed by the CeCILL license under French law and
# abiding by the rules of distribution of free software.  You can  use, 
# modify and/ or redistribute the software under the terms of the CeCILL
# license as circulated by CEA, CNRS and INRIA at the following URL
# "http://www.cecill.info". 
# 
# As a counterpart to the access to the source code and  rights to copy,
# modify and redistribute granted by the license, users are provided only
# with a limited warranty  and the software's author,  the holder of the
# economic rights,  and the successive licensors  have only  limited
# liability. 
# 
# In this respect, the user's attention is drawn to the risks associated
# with loading,  using,  modifying and/or developing or reproducing the
# software by the user in light of its specific status of free software,
# that may mean  that it is complicated to manipulate,  and  that  also
# therefore means  that it is reserved for developers  and  experienced
# professionals having in-depth computer knowledge. Users are therefore
# encouraged to load and test the software's suitability as regards their
# requirements in conditions enabling the security of their systems and/or 
# data to be ensured and,  more generally, to use and operate it in the 
# same conditions as regards security. 
# 
# The fact that you are presently reading this means that you have had
# knowledge of the CeCILL license and that you accept its terms.

"""This mdoule provides TLE data extraction tools."""

from operator import xor
import re
import logging
import csv
import datetime

logger = logging.getLogger("root")

def check_format(line1, line2):
    """Checks whether the two lines correspond to the TLE format or not.
    
    :param line1: First line of the TLE.
    :type line1: str
    :param line2: Second line of the TLE.
    :type line2: str
    :return: True if the lines corresponds to the TLE format, else False.
    :rtype: bool
    
    ..seealso:: :func:`check_integrity`
    ..warning:: This function checks only the format, not the content.
    """
    
    # The regular expressions matches the TLE format from the begining of the
    # lines, that is, all the characters after the 69th character will be
    # ignored and do not count for the format nor the conversion.
    tle_format = ("^1 \d\d\d\d\d[U ] \d\d\d\d\d([A-Z]  |[A-Z][A-Z] |[A-Z][A-Z][A-Z]) \d\d\d\d\d\.\d\d\d\d\d\d\d\d [\+\- ]\.\d\d\d\d\d\d\d\d [\+\- ]\d\d\d\d\d[+-]\d [\+\- ]\d\d\d\d\d[\+\-]\d \d (\d\d\d\d| \d\d\d|  \d\d|   \d)\d", "^2 \d\d\d\d\d (\d\d\d| \d\d|  \d)\.\d\d\d\d (\d\d\d| \d\d|  \d)\.\d\d\d\d \d\d\d\d\d\d\d (\d\d\d| \d\d|  \d)\.\d\d\d\d (\d\d\d| \d\d|  \d).\d\d\d\d \d\d\.\d\d\d\d\d\d\d\d(\d\d\d\d\d| \d\d\d\d|  \d\d\d|   \d\d|    \d)\d")
    
    tle_regex = (re.compile(tle_format[0], re.ASCII), re.compile(tle_format[1], re.ASCII))
    
    if tle_regex[0].match(line1) and tle_regex[1].match(line2):
        return True
    else:
        return False
    
def check_integrity(line):
    """Checks the integrity of the line by recalculating the checksum.
    
    The checksum at the end of a TLE line is the sum of all digits in the line
    (except the last character) added to the number of minus signs, modulo 10.
    
    For instance, in the following line:
    
        1 38873U 12044E   14001.28351472  .02538928  13044-2  14784-1 0  7464
    
    the sum of all digits (except the last 4) is 174, then the checksum is 4, as
    written at the end of the line.
    
    :param line: The line to validate the checksum of.
    :type line: str
    :return: True if the checksum is valid, else False.
    :rtype: bool
    
    ..seealso:: :func:`check_format`.
    """
    
    checksum = 0
    
    for character in line[0:-1]:
        if re.match("[0-9]", character):
            checksum += int(character)
        elif character == "-":
            checksum += 1
            
    checksum = checksum % 10
    
    logger.debug("Checksum: " + str(checksum) + " (calculated) / " + line[-1] + "(in the TLE).")
    
    if int(line[-1]) == checksum:
        return True
    else:
        return False

def epoch_to_datetime(epoch_str):
    """Converts the epoch string to a standardized datetime string.
    
    Epoch format: YYDDD.FFFFFFFF
    * YY: two last digits of the year (20YY if YY < 57, else 19YY)
    * DDD: number of the day in the year (1st jan. = 1)
    * FFFFFFFF: decimal part of the fraction of the day (noon = 0.5)
    
    :param epoch_str: The epoch string.
    :type epoch_str: str
    :return: Standard date string (YYYY-MM-DD hh:mm:ss).
    :rtype: str
    """
    
    epoch_year = epoch_str[0:2]
    epoch_day = epoch_str[2:5]
    epoch_dayfrac = float("0" + epoch_str[5:-1])
    
    if int(epoch_year) < 57:
        epoch_year = "20" + epoch_year
    else:
        epoch_year = "19" + epoch_year
        
    date = datetime.datetime.strptime(epoch_year + " " + epoch_day, "%Y %j")
    
    epoch_hour = 24 * epoch_dayfrac
    epoch_minute = 60 * (epoch_hour - int(epoch_hour))
    epoch_second = 60 * (epoch_minute - int(epoch_minute))
    
    epoch_hour = int(epoch_hour)
    epoch_minute = int(epoch_minute)
    epoch_second = int(epoch_second)
        
    return date.strftime("%Y-%m-%d") + " {hour}:{min}:{sec}".format(hour=epoch_hour, min=epoch_minute, sec=epoch_second)
    
def convert_tle(line1, line2):
    """Converts the TLE lines in a single dictionary.
    
    Abbreviations used in the dictionary:
    
    ========  =============================================
    Abbrev.   Signification
    ========  =============================================
    cospar    International or COSPAR designator / NSSDC ID
    epoch     Epoch time
    mmotdd    Mean motion second derivative
    mmotd     Mean motion derivative
    bstar     Radiation pressure coefficient
    ephtype   Ephemeris type
    eltnum    Element number
    inclin    Inclination
    raan      Right ascension of ascending node
    eccentr   Eccentricity
    argofper  Argument of perigee
    manomal   Mean anomaly
    mmot      Mean motion
    epochrev  Epoch revolution
    ========  =============================================
    
    :param line1: The first TLE line.
    :type line1: str
    :param line2: The second TLE line.
    :type line2: str
    :return: Dictionary of data strored in the ``line1`` and ``line2``.
    :rtype: dict
    
    ..warning:: The tle specifed in line1 and line2 must be valid.
    ..note:: This functions checks if the two lines belongs to the same satellite. The 
    """
    
    tle_data = {}
    
    # When the satellite number is different in the two lines, it means that the
    # given TLE is made from two lines from different satellites.
    if line1[2:7] == line2[2:7]:
        tle_data["satnum"] = line1[2:7]
        
        if line1[7] == "U":
            tle_data["satnum"] += "U"
            
        tle_data["cospar"] = line1[9:17].strip()
        logger.debug(line1[9:17].strip())
        tle_data["epoch"] = epoch_to_datetime(line1[18:32].strip())
        tle_data["mmotd"] = float(line1[33:43].strip())
        tle_data["mmotdd"] = float(line1[45].strip() + "0." + line1[45:50].strip() + "E" + line1[50:52])
        tle_data["bstar"] = float(line1[53].strip() + "0." + line1[54:59].strip() + "E" + line1[59:61])
        tle_data["ephtype"] = int(line1[62])
        tle_data["eltnum"] = line1[64:68].strip()
        tle_data["inclin"] = float(line2[8:16].strip())
        tle_data["raan"] = float(line2[17:25].strip())
        tle_data["eccentr"] = float("0." + line2[26:33].strip())
        tle_data["argofper"] = float(line2[34:42].strip())
        tle_data["manomaly"] = float(line2[43:51].strip())
        tle_data["mmot"] = float(line2[52:63].strip())
        tle_data["epochrev"] = int(line2[63:68].strip())
        
        return tle_data
    else:
        return None

def data_extract(cospar, tle_files, output_file):
    """Extracts orbital parameters for the given satellite from the given files.
    
    The function looks into the TLE files in order to find the TLEs of the
    satellite. Each found TLE is converted and the values are stored into a
    CSV file.
    
    The TLE files must be formatted like this:
    
        1 00005U 58002B   14001.18782563  .00000040  00000-0  40921-4 0  1802
        2 00005 034.2515 294.1619 1849340 178.4613 182.2758 10.84381573949160
        1 00011U 59001A   14001.49929578  .00000254  00000-0  11590-3 0   627
        2 00011 032.8774 265.3546 1476296 264.4994 078.6020 11.84019141336756
        1 00012U 59001B   14001.15043527  .00000935  00000-0  54042-3 0  7398
        2 00012 032.9115 320.5248 1673017 279.4922 062.1207 11.42639539252314
    
    :param cospar: International or COSPAR designator / NSSDC ID.
    :type cospar: str
    :param tle_files: List of TLE filenames and paths.
    :type tle_files: list
    :param output_file: path and filename of the CSV output file.
    :type output_file: str
    
    ..warning:: No blank lines before or in the middle of the files, no titles on the top of the TLEs.
    ..note:: When there is a problem at a certain TLE, this TLE is skipped.
    ..seealso:: :func:`convert_tle`
    """
    if cospar is not None:
        logger.info("Extracting data for " + cospar + ".")
    else:
        logger.info("Extracting all data in files:\n" + "\n".join(["\t" + file for file in tle_files]))
    
    # Initialization of the resulting array of values with the column headers.
    extracted_data = [["Satellite number", "COSPAR", "Epoch time", "Mean motion dot dot", "Mean motion dot", "BSTAR", "Ephemeris type", "Element number", "Inclination", "RAAN", "Eccentricity", "Argument of perigee", "Mean anomaly", "Mean motion", "Epoch rev"]]
        
    for tle_file in tle_files:
        logger.debug("Opening " + tle_file + ".")
        try:
            file = open(tle_file, "r")
            lines = file.readlines()
            file.close()
        except FileNotFoundError:
            logger.error("Unable to find " + tle_file + ".")
            continue
        else:
            logger.debug("Successfuly loaded the file.")
        
        i = 0
        
        while i + 1 < len(lines):
            logger.debug("Scaning lines " + str(i + 1) + " and " + str(i + 2) + ".")
            tle = (lines[i].strip(), lines[i + 1].strip())
            
            good_to_extract = True
            
            if check_format(*tle):
                logger.debug("Good format.")
                if not check_integrity(tle[0]):
                    good_to_extract = False
                    logger.error("In " + tle_file + ", line " + str(i + 1) + ": checksum verification failed.")
                else:
                    logger.debug("Checksum verification succeed.")
                
                if not check_integrity(tle[1]):
                    good_to_extract = False
                    logger.error("In " + tle_file + ", line " + str(i + 2) + ": checksum verification failed.")
                else:
                    logger.debug("Checksum verification succeed.")
            else:
                good_to_extract = False
                logger.error("In " + tle_file + ", lines " + str(i + 1) + " and " + str(i + 2) + ": bad format.")
            
            if good_to_extract:
                logger.debug("Convert TLE in lines " + str(i + 1) + " and " + str(i + 2) + ".")
                tle_data = convert_tle(*tle)
                
                if tle_data is None:
                    logger.error("Different satellite number for lines " + str(i + 1) + " and " + str(i + 2) + ".")
                elif tle_data["cospar"] == cospar or cospar is None:
                    logger.debug("This TLE corresponds to the asked satellite.")
                    
                    data_line = [tle_data["satnum"]]
                    data_line.append(tle_data["cospar"])
                    data_line.append(tle_data["epoch"])
                    data_line.append(tle_data["mmotd"])
                    data_line.append(tle_data["mmotdd"])
                    data_line.append(tle_data["bstar"])
                    data_line.append(tle_data["ephtype"])
                    data_line.append(tle_data["eltnum"])
                    data_line.append(tle_data["inclin"])
                    data_line.append(tle_data["raan"])
                    data_line.append(tle_data["eccentr"])
                    data_line.append(tle_data["argofper"])
                    data_line.append(tle_data["manomaly"])
                    data_line.append(tle_data["mmot"])
                    data_line.append(tle_data["epochrev"])
                    
                    extracted_data.append(data_line)
                else:
                    logger.debug("This TLE does not correspond to the asked satellite.")
                
            i = i + 2
    
    try:
        csv_output_file = csv.writer(open(output_file, "w", newline=""))
    except PermissionError:
        logger.error("Impossible to write in " + output_file + ".")
    else:
        if len(extracted_data) < 2: # Only the column headers line.
            logger.warning("There was no data extracted. " + output_file + " won't be created.")
            return False
        else:
            for line in extracted_data:
                csv_output_file.writerow(line)
        
            logger.info("Wrote " + output_file + ".")
            return True
        
