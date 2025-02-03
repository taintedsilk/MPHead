using VRCFaceTracking;
using VRCFaceTracking.Core.Params.Data;
using VRCFaceTracking.Core.Params.Expressions;
using VRCFaceTracking.Core.Types;

namespace MediaPipeWebcamModule
{
    
    public class MediaPipeWebcamTracker : ExtTrackingModule
    {
        private readonly Dictionary<int, (string Name, float Multiplier)> UEtranslation = new()
        {
            // Tongue
            {(int)UnifiedExpressions.TongueOut, ("tongueOut", 1)},

            // Jaw
            {(int)UnifiedExpressions.JawOpen, ("jawOpen", 1)},
            {(int)UnifiedExpressions.JawLeft, ("jawLeft", 1)},
            {(int)UnifiedExpressions.JawRight, ("jawRight", 1)},
            {(int)UnifiedExpressions.JawForward, ("jawForward", 1)},

            // Nose
            {(int)UnifiedExpressions.NoseSneerLeft, ("noseSneerLeft", 1)},
            {(int)UnifiedExpressions.NoseSneerRight, ("noseSneerRight", 1)},

            // Mouth
            {(int)UnifiedExpressions.MouthClosed, ("mouthClose", 1)},

            // Lip Puckers
            {(int)UnifiedExpressions.LipPuckerLowerLeft, ("mouthPucker", 1)},
            {(int)UnifiedExpressions.LipPuckerLowerRight, ("mouthPucker", 1)},
            {(int)UnifiedExpressions.LipPuckerUpperLeft, ("mouthPucker", 1)},
            {(int)UnifiedExpressions.LipPuckerUpperRight, ("mouthPucker", 1)},

            // Lip Funnels
            {(int)UnifiedExpressions.LipFunnelLowerLeft, ("mouthFunnel", 1)},
            {(int)UnifiedExpressions.LipFunnelLowerRight, ("mouthFunnel", 1)},
            {(int)UnifiedExpressions.LipFunnelUpperLeft, ("mouthFunnel", 1)},
            {(int)UnifiedExpressions.LipFunnelUpperRight, ("mouthFunnel", 1)},

            // Mouth Movements
            {(int)UnifiedExpressions.MouthUpperUpLeft, ("mouthUpperUpLeft", 1)},
            {(int)UnifiedExpressions.MouthUpperUpRight, ("mouthUpperUpRight", 1)},
            {(int)UnifiedExpressions.MouthLowerDownLeft, ("mouthLowerDownLeft", 1)},
            {(int)UnifiedExpressions.MouthLowerDownRight, ("mouthLowerDownRight", 1)},
            {(int)UnifiedExpressions.MouthPressLeft, ("mouthPressLeft", 1)},
            {(int)UnifiedExpressions.MouthPressRight, ("mouthPressRight", 1)},
            {(int)UnifiedExpressions.MouthStretchLeft, ("mouthStretchLeft", 1)},
            {(int)UnifiedExpressions.MouthStretchRight, ("mouthStretchRight", 1)},
            {(int)UnifiedExpressions.MouthDimpleLeft, ("mouthDimpleLeft", 1)},
            {(int)UnifiedExpressions.MouthDimpleRight, ("mouthDimpleRight", 1)},
            {(int)UnifiedExpressions.MouthCornerPullLeft, ("mouthSmileLeft", 1)},
            {(int)UnifiedExpressions.MouthCornerPullRight, ("mouthSmileRight", 1)},
            {(int)UnifiedExpressions.MouthFrownLeft, ("mouthFrownLeft", 1)},
            {(int)UnifiedExpressions.MouthFrownRight, ("mouthFrownRight", 1)},

            // Cheeks
            {(int)UnifiedExpressions.CheekPuffLeft, ("cheekPuff", 1)},
            {(int)UnifiedExpressions.CheekPuffRight, ("cheekPuff", 1)},
            {(int)UnifiedExpressions.CheekSquintLeft, ("cheekSquintLeft", 1)},
            {(int)UnifiedExpressions.CheekSquintRight, ("cheekSquintRight", 1)},

            // Brows
            {(int)UnifiedExpressions.BrowInnerUpLeft, ("browInnerUp", 1)},
            {(int)UnifiedExpressions.BrowInnerUpRight, ("browInnerUp", 1)},
            {(int)UnifiedExpressions.BrowLowererLeft, ("browDownLeft", 1)},
            {(int)UnifiedExpressions.BrowLowererRight, ("browDownRight", 1)},
            {(int)UnifiedExpressions.BrowOuterUpLeft, ("browOuterUpLeft", 1)},
            {(int)UnifiedExpressions.BrowOuterUpRight, ("browOuterUpRight", 1)},

            // Eyes
            {(int)UnifiedExpressions.EyeSquintLeft, ("eyeSquintLeft", 1)},
            {(int)UnifiedExpressions.EyeSquintRight, ("eyeSquintRight", 1)},
            {(int)UnifiedExpressions.EyeWideLeft, ("eyeWideLeft", 1)},
            {(int)UnifiedExpressions.EyeWideRight, ("eyeWideRight", 1)},
                // Cheeks
            {(int)UnifiedExpressions.CheekSuckLeft, ("cheekSuckLeft", 1)},
            {(int)UnifiedExpressions.CheekSuckRight, ("cheekSuckRight", 1)},

            // Mouth
            {(int)UnifiedExpressions.MouthUpperLeft, ("mouthLeft", 1)},
            {(int)UnifiedExpressions.MouthUpperRight, ("mouthRight", 1)},
            {(int)UnifiedExpressions.LipSuckLowerLeft, ("mouthRollLower", 1)},
            {(int)UnifiedExpressions.LipSuckLowerRight, ("mouthRollLower", 1)},
            {(int)UnifiedExpressions.LipSuckUpperLeft, ("mouthRollUpper", 1)},
            {(int)UnifiedExpressions.LipSuckUpperRight, ("mouthRollUpper", 1)},
            {(int)UnifiedExpressions.MouthRaiserLower, ("mouthShrugLower", 1)},
            {(int)UnifiedExpressions.MouthRaiserUpper, ("mouthShrugUpper", 1)},

            // Tongue
            {(int)UnifiedExpressions.TongueBendDown, ("tongueBendDown", 1)},
            {(int)UnifiedExpressions.TongueCurlUp, ("tongueCurlUp", 1)},
            {(int)UnifiedExpressions.TongueDown, ("tongueDown", 1)},
            {(int)UnifiedExpressions.TongueFlat, ("tongueFlat", 1)},
            {(int)UnifiedExpressions.TongueLeft, ("tongueLeft", 1)},
            {(int)UnifiedExpressions.TongueRight, ("tongueRight", 1)},
            {(int)UnifiedExpressions.TongueRoll, ("tongueRoll", 1)},
            {(int)UnifiedExpressions.TongueSquish, ("tongueSquish", 1)},
            {(int)UnifiedExpressions.TongueTwistLeft, ("tongueTwistLeft", 1)},
            {(int)UnifiedExpressions.TongueTwistRight, ("tongueTwistRight", 1)},
            {(int)UnifiedExpressions.TongueUp, ("tongueUp", 1)},

            // Head 
            /// Head rotation values should be normalized to a [-1, 1] range representing -90d to 90d rotation (0 meaning facing directly forwards)
            /// Head position values should be normalized / capped to a [-1, 1] range and represent deviation from a set user origin point in meters
            ///     The normalized values should be *approximately* represent a 1x1x1 meter movement region about the user's origin point 
            ///     Head position coordinates should be *LEFT handed, Y-up* (matching Unity coordinate system)
            ///     (i.e. HeadPosX = 1 means the user is 0.5m to their right from their starting point, HeadPosX = -1 the user is 0.5m to their left)
        };

        private TcpReceiver _receiver;

        public override (bool SupportsEye, bool SupportsExpression) Supported => (true, true);

        public override (bool eyeSuccess, bool expressionSuccess) Initialize(bool eyeAvailable, bool expressionAvailable)
        {
            ModuleInformation.Name = "Mediapipe Webcam Module";
            _receiver = new TcpReceiver(12345);
            return (eyeAvailable, expressionAvailable);
        }


        public override void Update()
        {
            var trackingData = _receiver.GetOldestMessage();
            if (trackingData == null)
            {
                Thread.Sleep(10);
                return;
            }

            // Update expression parameters with multipliers
            foreach (var param in UEtranslation)
            {
                if (trackingData.TryGetValue(param.Value.Name, out float value))
                    UnifiedTracking.Data.Shapes[param.Key].Weight = value * param.Value.Multiplier;
            }

            // Update eye openness with TryGetValue
            if (trackingData.TryGetValue("eyeBlinkLeft", out float eyeBlinkLeft))
                UnifiedTracking.Data.Eye.Left.Openness = 1 - eyeBlinkLeft;
            if (trackingData.TryGetValue("eyeBlinkRight", out float eyeBlinkRight))
                UnifiedTracking.Data.Eye.Right.Openness = 1 - eyeBlinkRight;

            // Update eye gaze with TryGetValue
            if (trackingData.TryGetValue("eyeLookOutLeft", out float eyeLookOutLeft) &&
                trackingData.TryGetValue("eyeLookInLeft", out float eyeLookInLeft))
            {
                UnifiedTracking.Data.Eye.Left.Gaze.x = (eyeLookOutLeft - eyeLookInLeft);
            }

            if (trackingData.TryGetValue("eyeLookUpLeft", out float eyeLookUpLeft) &&
                trackingData.TryGetValue("eyeLookDownLeft", out float eyeLookDownLeft))
            {
                UnifiedTracking.Data.Eye.Left.Gaze.y = (eyeLookUpLeft - eyeLookDownLeft);
            }

            if (trackingData.TryGetValue("eyeLookInRight", out float eyeLookInRight) &&
                trackingData.TryGetValue("eyeLookOutRight", out float eyeLookOutRight))
            {
                UnifiedTracking.Data.Eye.Right.Gaze.x = (eyeLookInRight - eyeLookOutRight);
            }

            if (trackingData.TryGetValue("eyeLookUpRight", out float eyeLookUpRight) &&
                trackingData.TryGetValue("eyeLookDownRight", out float eyeLookDownRight))
            {
                UnifiedTracking.Data.Eye.Right.Gaze.y = (eyeLookUpRight - eyeLookDownRight);
            }

            // Update head rotation and position with checks
            if (trackingData.TryGetValue("headPitch", out float headPitch))
                UnifiedTracking.Data.Head.HeadPitch = headPitch;
            if (trackingData.TryGetValue("headYaw", out float headYaw))
                UnifiedTracking.Data.Head.HeadYaw = headYaw;
            if (trackingData.TryGetValue("headRoll", out float headRoll))
                UnifiedTracking.Data.Head.HeadRoll = headRoll;

            if (trackingData.TryGetValue("headX", out float headX))
                UnifiedTracking.Data.Head.HeadPosX = headX;
            if (trackingData.TryGetValue("headY", out float headY))
                UnifiedTracking.Data.Head.HeadPosY = headY;
            if (trackingData.TryGetValue("headZ", out float headZ))
                UnifiedTracking.Data.Head.HeadPosZ = headZ;
            Thread.Sleep(10);
        }

        public override void Teardown() => _receiver?.Stop();
    }
}