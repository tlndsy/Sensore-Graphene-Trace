from django.utils.text import re_camel_case

from user.models import *
import csv
import numpy as np

class ScanInterpreter():

    def scanDataFile(self, file):
        try:
            with file.open(mode = 'r') as f:
                dataFile = csv.reader(f)
                scan = []
                for line in dataFile:
                    scan.append(line)

                return scan
        except FileNotFoundError:
            scan = []
            i = 0
            while i < 32:
                scan.append(["0", "0", "0", "0", "0", "0", "0", "0","0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0","0", "0", "0", "0","0", "0", "0", "0","0", "0", "0", "0"])
                i = i + 1
            return scan

    def getData(self, testNo, scannedData, convertToInt = True):
        # Retrieve a scan from the scan file. Only gives one file.
        retrievedData = []
        i = testNo * 32
        endTest = (testNo + 1) * 32
        if len(scannedData) < endTest:
            return -1
        while i < endTest:
            retrievedData.append(scannedData[i])
            i = i + 1

        if convertToInt:
            intData = []
            lineCount = 0
            for line in retrievedData:
                entryCount = 0
                intLine = line
                for entry in line:
                    intLine[entryCount] = int(entry)
                    entryCount += 1
                intData.append(intLine)
                lineCount = lineCount + 1
            return intData
        else:
            return retrievedData

    def locateArea(self, x, y):
        if x < 13 and y > 10 and y < 30:  # Try to identify a specific area
            area = "Left Cheek"
        elif x > 19 and y > 10 and y < 30:
            area = "Right Cheek"
        elif x < 16 and y < 16:  # Generic areas if specific areas aren't located
            area = "Upper Left"
        elif x < 16 and y >= 16:
            area = "Lower Left"
        elif x >= 16 and y < 16:
            area = "Upper Right"
        elif x >= 16 and y >= 16:
            area = "Lower Right"
        return area

    def checkSeverity(self, pressure):
        # Determine the severity of the highest pressure point detected
        if pressure > 400:
            severity = "Very High"
        elif pressure > 250:
            severity = "High"
        elif pressure > 150:
            severity = "Moderate"
        else:
            severity = "Low"

        return severity

    def showScan(self, scan):
        # Used for testing, currently not in usage
        i = 0
        while i < 32:
            j = 0
            while j < 32:
                checkedNumber = scan[i][j]
                if len(checkedNumber) == 1:
                    checkedNumber = " " + checkedNumber + " "
                elif len(checkedNumber) == 2:
                    checkedNumber = " " + checkedNumber
                scan[i][j] = checkedNumber
                j += 1

            line = " ".join(scan[i][:])
            print(line)
            i += 1

    def makeRecommendation(self, severity):
        recommendation = " "
        if severity == "Low":
            recommendation = "no action needs to be taken, and you are not at significant risk of ulcers"
        elif severity == "Moderate":
            recommendation = "this area should be monitored for possible issues, as you may be at risk of developing ulcers"
        elif severity == "High":
            recommendation = "this area should be monitored closely, as you are at risk of developing ulcers"
        elif severity == "Very High":
            recommendation = "preventative action should be taken to prevent issues, as you will likely develop ulcers in this area if not treated"
        return recommendation

    def createReport(self, pressureValue, xCoord, yCoord, highestScan):
        # Give a description of the pressure sensitivity
        location = self.locateArea(xCoord, yCoord)
        severity = self.checkSeverity(int(pressureValue))
        recommendation = self.makeRecommendation(severity)
        report = ["", "", "", ""]
        report[0] = "The highest point of pressure on your scan is detected in the " + location + " area."
        report[1] = "This is a pressure value of " + str(pressureValue) + ", which is a " + severity + " pressure reading."
        report[2] = "This pressure value means that " + recommendation + "."
        report[3] = ("The exact coordinates of this pressure point on the scan are (" + str(xCoord) + "," + str(yCoord) +
                     "), and this happened on snapshot " + str(highestScan) + ".")
        return report, severity

    def processFrame(self, currentScan, totalHighestValue, highestValueRowIndex, highestScanIndex, frameNumber):
        frameHighestValue = 0
        currentRowIndex = 0
        frameHighestRowIndex = 0
        for row in currentScan:
            rowHighestValue = max(row)
            if rowHighestValue > frameHighestValue:
                frameHighestValue = rowHighestValue
                frameHighestRowIndex = currentRowIndex
            currentRowIndex += 1

        if frameHighestValue > totalHighestValue:
            totalHighestValue = frameHighestValue
            highestScanIndex = frameNumber
            highestValueRowIndex = frameHighestRowIndex

        return highestScanIndex, totalHighestValue, highestValueRowIndex

    def runInterpreter(self, file):
        scannedData = self.scanDataFile(file)

        totalHighestValue = 0
        highestScanIndex = 0
        endLoop = False
        frameNumber = 0
        highestValueRowIndex = 0

        while not endLoop:
            currentScan = self.getData(frameNumber, scannedData)

            if currentScan == -1:
                endLoop = True
            else:
                highestScanIndex, totalHighestValue, highestValueRowIndex \
                    = self.processFrame(currentScan, totalHighestValue, highestValueRowIndex,
                                        highestScanIndex, frameNumber)
                frameNumber += 1

        highestScanData = self.getData(highestScanIndex, scannedData)
        highestValueRow = highestScanData[highestValueRowIndex]

        highestXCoord = highestValueRow.index(totalHighestValue)
        highestYCoord = highestScanData.index(highestValueRow)

        report, severity = self.createReport(totalHighestValue, highestXCoord, highestYCoord, highestScanIndex)

        if severity == "Very High":
            triggerFlag = True
        else:
            triggerFlag = False
        return report, highestScanIndex, triggerFlag

    # Takes the report frame and generates a heatmap
    def get_pressure_matrix(self, file, frame):
        scannedData = self.scanDataFile(file)
        frameScan = self.getData(frame, scannedData, False)
        intScan = []
        for line in frameScan:
            intLine = list(map(int, line))
            for entry in intLine:
                intScan.append(entry)
        return intScan

    def generate_report(self, current_reading):
        report = Report(pressure_map_reading=current_reading)
        reportContents, scanNumber, triggerFlag = self.runInterpreter(current_reading.pressure_reading)
        report.content = "@".join(reportContents)
        report.frame = scanNumber
        report.pressure_alert = triggerFlag
        report.read_receipt = False
        report.save()
        return report

    def checkReportInRange(self, reportNumber, noOfReadings):
        if reportNumber >= noOfReadings and noOfReadings > 0:
            reportNumber = noOfReadings - 1
        elif reportNumber < 0:
            reportNumber = 0
        return reportNumber

    def returnEmptyPage(self):
        reportContents = ["", "", ""]

        reportContents[0] = "The report you have requested cannot be found."
        reportContents[1] = "This could be because there are no scans on file for this user, or another error."
        reportContents[2] = "Please contact your administrator if you believe this is in error."

        context = {"report_0": reportContents[0], "report_1": reportContents[1], "report_2": reportContents[2],
                   "reportNumber": 0, "noOfReports": 0, "allReports": []}

        return context
