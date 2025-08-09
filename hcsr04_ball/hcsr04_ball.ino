#include <NewPing.h>
#define trig1 2
#define echo1 3
#define trig2 4
#define echo2 5
#define trig3 6
#define echo3 7
#define max_distance 50
int d1;
int d2;
int d3;

const int wall1=40;
const int wall2=40;
const int wall3=30;

NewPing sonar1(trig1,echo1,max_distance);
NewPing sonar2(trig2,echo2,max_distance);
NewPing sonar3(trig3,echo3,max_distance);

void setup() {
  Serial.begin(115200);
  delay(2000); // Give time for serial to initialize
}

void loop() {
  d1=sonar1.ping_cm();
  d2=sonar2.ping_cm();
  d3=sonar3.ping_cm();
  
  // Replace 0 readings with a default wall distance
  if(d1==0) d1=wall1;
  if(d2==0) d2=wall2;
  if(d3==0) d3=wall3;

  // Print distances in a comma-separated format for Python
  Serial.print(d1);
  Serial.print(",");
  Serial.print(d2);
  Serial.print(",");
  Serial.println(d3);

  delay(100);
}