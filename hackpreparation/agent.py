def check_refund(amount): #this function expects us to provide a value when we call it 
    refund=int(input("enter the refund amount:"))
    if amount<=2000:
        return "ALLOW"
    else:
        return "BLOCK"
print(check_refund(1000)) 

