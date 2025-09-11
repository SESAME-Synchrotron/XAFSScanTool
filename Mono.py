import numpy as np

# you can add any offline mono operation to this class
    
class DCM():
    @staticmethod
    def energySpeed(startPoint, stepSize, overAllTime):
        thetaStepSize = abs(DCM.getThetaPosition(startPoint) - DCM.getThetaPosition(startPoint + stepSize))
        stepMovementTime = overAllTime
        speed = thetaStepSize/stepMovementTime
        return speed

    @staticmethod
    def getThetaPosition(energy):
        P = 1.9770410767
        theta = np.degrees(np.arcsin(P / energy))
        return theta 