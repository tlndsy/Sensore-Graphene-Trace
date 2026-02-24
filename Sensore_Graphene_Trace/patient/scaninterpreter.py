from user.models import *
import csv
import numpy as np

class ScanInterpreter():

    def scanDataFile(self, fileName):
        try:
            with open(fileName, mode = 'r') as file:
                dataFile = csv.reader(file)
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

    def createReport(self, pressureValue, xCoord, yCoord):
        location = self.locateArea(self, xCoord, yCoord)
        severity = self.checkSeverity(self, int(pressureValue))
        report = ["", "", ""]
        report[0] = "An area of " + severity + " pressure is detected in the " + location + " area."
        report[1] = "The pressure value is " + str(pressureValue) + "."
        report[2] = "The exact coordinates of the pressure point on the scan are (" + str(xCoord) + "," + str(yCoord) + ")."
        return report

    def runInterpreter(self, fileAddress):
        scannedData = self.scanDataFile(self, fileAddress)
        testScan = self.getTestData(self,0, scannedData)
        self.showScan(self, testScan)

        highestValueRow = max(testScan)
        highestValue = max(highestValueRow)

        highestXCoord = highestValueRow.index(highestValue)
        highestYCoord = testScan.index(highestValueRow)

        report = self.createReport(self, highestValue, highestXCoord, highestYCoord)
        return report