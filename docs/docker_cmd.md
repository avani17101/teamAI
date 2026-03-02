Status Summary                                                                                  
  ┌────────────────────┬──────────────────────┐                                                   
  │     Component      │        Status        │                                                   
  ├────────────────────┼──────────────────────┤                                                   
  │ Container          │ Running & Healthy    │                                                   
  ├────────────────────┼──────────────────────┤                                                   
  │ FastAPI Backend    │ Running on port 8001 │                                                   
  ├────────────────────┼──────────────────────┤                                                   
  │ K2 API             │ Ready                │                                                   
  ├────────────────────┼──────────────────────┤                                                   
  │ Email Forwarder    │ Polling active       │                                                   
  ├────────────────────┼──────────────────────┤                                                   
  │ Reminder Scheduler │ Running              │                                                   
  └────────────────────┴──────────────────────┘                                                   
  Test in Browser                                                                                 
                                                                                                  
  open http://localhost:8001                                                                      
                                                                                                  
  Useful Commands                                                                                 
                                                                                                  
  # View logs                                                                                     
  docker logs teamai-app -f                                                                       
                                                                                                  
  # Stop                                                                                          
  docker-compose down                                                                             
                                                                                                  
  # Restart                                                                                       
  docker-compose restart                                                                          
                                                                                                  
  # Rebuild after code changes                                                                    
  docker-compose up -d --build    