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
                scan.append(["0", "0", "0", "0","0", "0", "0", "0","0", "0", "0", "0","0", "0", "0", "0", "0", "0", "0", "0","0", "0", "0", "0","0", "0", "0", "0","0", "0", "0", "0"])
                i = i + 1
            return scan

    def getTestData(self, testNo, scannedData):
        testScan = []
        i = testNo * 32
        endTest = (testNo + 1) * 32
        while i < endTest:
            testScan.append(scannedData[i])
            i = i + 1

        return testScan

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
        if pressure > 400:
            severity = "Extremely High"
        elif pressure > 250:
            severity = "Very High"
        elif pressure > 150:
            severity = "High"
        else:
            severity = "Normal"

        return severity

    def showScan(self, scan):
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
        if severity == "Normal":
            recommendation = "no action needs to be taken, and you are not at significant risk of ulcers"
        elif severity == "High":
            recommendation = "this area should be monitored for possible issues, as you may be at risk of developing ulcers"
        elif severity == "Very High":
            recommendation = "this area should be monitored closely, as you are at risk of developing ulcers"
        elif severity == "Extremely High":
            recommendation = "preventative action should be taken to prevent issues, as you will likely develop ulcers in this area if not corrected"
        return recommendation

    def createReport(self, pressureValue, xCoord, yCoord):
        location = self.locateArea(self, xCoord, yCoord)
        severity = self.checkSeverity(self, int(pressureValue))
        recommendation = self.makeRecommendation(self, severity)
        report = ["", "", "", ""]
        report[0] = "The highest point of pressure on your scan is detected in the " + location + " area."
        report[1] = "This is a value of " + str(pressureValue) + ", which is a " + severity + " pressure reading."
        report[2] = "This pressure value means that " + recommendation + "."
        report[3] = "The exact coordinates of the pressure point on the scan are (" + str(xCoord) + "," + str(yCoord) + ")."
        return report

    def runInterpreter(self, file):
        scannedData = self.scanDataFile(self, file)
        testScan = self.getTestData(self,0, scannedData)
        self.showScan(self, testScan)

        highestValueRow = max(testScan)
        highestValue = max(highestValueRow)

        highestXCoord = highestValueRow.index(highestValue)
        highestYCoord = testScan.index(highestValueRow)

        report = self.createReport(self, highestValue, highestXCoord, highestYCoord)
        return report