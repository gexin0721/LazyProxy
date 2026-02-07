FUNCTION_BLOCK FB_MotorControlWithPID
VAR_INPUT
    // 电机控制输入
    Start : BOOL;                    // 启动信号
    Stop : BOOL;                     // 停止信号
    EmergencyStop : BOOL;            // 急停信号
    
    // PID控制输入
    Setpoint : REAL;                 // 设定值
    Feedback : REAL;                 // 反馈值
    EnablePID : BOOL;                // PID使能
    
    // PID参数
    Kp : REAL := 1.0;                // 比例增益
    Ki : REAL := 0.1;                // 积分增益
    Kd : REAL := 0.05;               // 微分增益
    MaxOutput : REAL := 100.0;       // 最大输出限制
    MinOutput : REAL := -100.0;      // 最小输出限制
    MaxIntegral : REAL := 100.0;     // 积分抗饱和限制
END_VAR

VAR_OUTPUT
    MotorRunning : BOOL;             // 电机运行状态
    PIDOutput : REAL;                // PID输出值
    Command : REAL;                  // 最终控制命令
    Error : REAL;                    // 当前误差
END_VAR

VAR
    // PID控制变量
    Integral : REAL := 0.0;          // 积分项
    PrevError : REAL := 0.0;         // 上次误差
    Derivative : REAL := 0.0;        // 微分项
    
    // 状态变量
    bMotorEnabled : BOOL := FALSE;   // 电机使能状态
END_VAR

// 电机启停控制逻辑
IF Start AND NOT EmergencyStop THEN
    bMotorEnabled := TRUE;
END_IF;

IF Stop OR EmergencyStop THEN
    bMotorEnabled := FALSE;
    // 停止时复位PID变量
    Integral := 0.0;
    PrevError := 0.0;
END_IF;

MotorRunning := bMotorEnabled;

// PID控制逻辑
IF bMotorEnabled AND EnablePID THEN
    // 计算误差
    Error := Setpoint - Feedback;
    
    // 积分项计算（带抗饱和）
    Integral := Integral + Error;
    IF Integral > MaxIntegral THEN
        Integral := MaxIntegral;
    ELSIF Integral < -MaxIntegral THEN
        Integral := -MaxIntegral;
    END_IF;
    
    // 微分项计算
    Derivative := Error - PrevError;
    
    // PID输出计算
    PIDOutput := Kp * Error + Ki * Integral + Kd * Derivative;
    
    // 输出钳位
    IF PIDOutput > MaxOutput THEN
        Command := MaxOutput;
    ELSIF PIDOutput < MinOutput THEN
        Command := MinOutput;
    ELSE
        Command := PIDOutput;
    END_IF;
    
    // 更新上次误差
    PrevError := Error;
ELSE
    // PID未使能时输出为0
    Command := 0.0;
    PIDOutput := 0.0;
    Error := 0.0;
END_IF;

END_FUNCTION_BLOCK
