from app.policy import assess_request
#import the function assess_request from the python module app.policy
#test checks one particular expectation of our code 
#eg:if our speaker doesnt not match it must return block 

#we need three things for that 1.arrange:prepare the inputs for those situations 2.act:call the particular function whith those inputs
#3.assert:checks whether is decision is blocked   

def test_unverified_speaker_is_blocked(): #expectation block 
#this defines the function that pytest can discover because its name starst from test_ here we arent passing any argiements to the function
    result = assess_request(action_type="payment",speaker_decision="no_match",deepfake_verdict="real",)
#we are calling our security function which is present in app/policy.py and saving its returned dictonary in RESULT
    assert result["decision"] == "BLOCK"
#checking the result 
#assert==>makes the test fail if the expectation is false , result==>it is dictonary returned by the policy function 
#["decsion"] accesses the value stored under "decision" key 

def test_fake_audio_is_blocked():
    result=assess_request(action_type="payment", speaker_decision="match", deepfake_verdict="fake",)
    #had i put the speaker_decision to no_match then our function would have returned and not checked deefake verdict 
    assert result["decision"] == "BLOCK"