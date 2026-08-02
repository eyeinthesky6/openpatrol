// OpenPatrol Security Sensor Hub Rev A reference firmware.
// Prototype source only; calibrate every zone against the installed loop.
#include <Arduino.h>
#include <SPI.h>

static const uint8_t CS_PIN=5, STROBE_PIN=6, SIREN_PIN=7, TAMPER_PIN=8, ISOLATE_PIN=9;
static const uint32_t MAX_OUTPUT_MS=60000;
uint32_t seqNo=0, strobeUntil=0, sirenUntil=0, lastHeartbeat=0;
String inputLine;
const char* lastState[8]={"unknown","unknown","unknown","unknown","unknown","unknown","unknown","unknown"};

int readMcp3008(uint8_t channel){
  digitalWrite(CS_PIN,LOW);
  SPI.transfer(0x01);
  int high=SPI.transfer(0x80 | (channel<<4));
  int low=SPI.transfer(0x00);
  digitalWrite(CS_PIN,HIGH);
  return ((high & 0x03)<<8)|low;
}
const char* classify(int raw){
  if(raw<80)return "short";
  if(raw<330)return "alarm";
  if(raw<760)return "normal";
  return "open";
}
void emitZone(int zone,const char* state,int raw){
  Serial.print("{\"v\":1,\"seq\":");Serial.print(++seqNo);Serial.print(",\"type\":\"zone\",\"zone\":");Serial.print(zone);
  Serial.print(",\"state\":\"");Serial.print(state);Serial.print("\",\"raw\":");Serial.print(raw);Serial.print(",\"at_ms\":");Serial.print(millis());Serial.println("}");
}
void setOutputs(bool strobe,bool siren,uint32_t seconds){
  if(digitalRead(ISOLATE_PIN)==LOW){strobe=false;siren=false;}
  uint32_t until=millis()+min(seconds*1000UL,MAX_OUTPUT_MS);
  digitalWrite(STROBE_PIN,strobe?HIGH:LOW);digitalWrite(SIREN_PIN,siren?HIGH:LOW);
  strobeUntil=strobe?until:0;sirenUntil=siren?until:0;
}
void handleLine(String line){
  // Deliberately tiny parser: only fixed allow-listed action tokens and integer seconds.
  uint32_t seconds=10;int p=line.indexOf("\"seconds\":");if(p>=0)seconds=(uint32_t)line.substring(p+10).toInt();
  if(line.indexOf("\"action\":\"strobe\"")>=0)setOutputs(true,false,seconds);
  else if(line.indexOf("\"action\":\"siren\"")>=0)setOutputs(false,true,seconds);
  else if(line.indexOf("\"action\":\"stop_output\"")>=0)setOutputs(false,false,0);
}
void setup(){
  Serial.begin(115200);pinMode(CS_PIN,OUTPUT);digitalWrite(CS_PIN,HIGH);SPI.begin();
  pinMode(STROBE_PIN,OUTPUT);pinMode(SIREN_PIN,OUTPUT);pinMode(TAMPER_PIN,INPUT_PULLUP);pinMode(ISOLATE_PIN,INPUT_PULLUP);setOutputs(false,false,0);
}
void loop(){
  while(Serial.available()){char c=(char)Serial.read();if(c=='\n'){handleLine(inputLine);inputLine="";}else if(c!='\r'&&inputLine.length()<512)inputLine+=c;}
  for(int i=0;i<8;i++){int raw=readMcp3008(i);const char* state=classify(raw);if(strcmp(state,lastState[i])!=0){lastState[i]=state;emitZone(i+1,state,raw);}}
  if(strobeUntil&&millis()>strobeUntil){digitalWrite(STROBE_PIN,LOW);strobeUntil=0;}if(sirenUntil&&millis()>sirenUntil){digitalWrite(SIREN_PIN,LOW);sirenUntil=0;}
  if(millis()-lastHeartbeat>5000){lastHeartbeat=millis();Serial.print("{\"v\":1,\"seq\":");Serial.print(++seqNo);Serial.print(",\"type\":\"heartbeat\",\"outputs\":{\"strobe\":");Serial.print(digitalRead(STROBE_PIN)?"true":"false");Serial.print(",\"siren\":");Serial.print(digitalRead(SIREN_PIN)?"true":"false");Serial.print("},\"tamper\":");Serial.print(digitalRead(TAMPER_PIN)==LOW?"true":"false");Serial.print(",\"at_ms\":");Serial.print(millis());Serial.println("}");}
  delay(100);
}
