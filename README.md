# Peer-to-Peer Servers Monitoring

## Roles
### Master
>* Sends heartbeats every 2 seconds over UDP
>* Maintains the global serversData and userRequests
>* Responds to slave requests for state via TCP
>* Handles new connections and updates the cluster view
>* Notifies slaves on disconnection

### Slave
>* On startup, sends a UDP JoinRequest broadcast
>* Receives JoinResponse with cluster and server data
>* Polls the master every second for state (FetchState over TCP)
>* Forwards user operations to the master

## Communication Between Peers
### UDP Broadcast Messages
>* JoinRequest: Sent by slave on startup or reconnect
>* Heartbeat: Sent by master every 2 seconds
>* LeaveNotification: When a node exits gracefully
>* ForceMaster: When an admin triggers a master takeover
>* masterDisconnected / slaveDisconnected: Used to notify about disconnections

### TCP Unicast Messages
>* FetchState: Slave → Master
>* StateUpdate: Master → Slave (response to fetch)
>
> All nodes maintain a clusterView, which tracks the role (master/slave) and IP of each connected peer.

## Frontend-Backend Interaction
### Frontend → Backend (HTTP POST)
> **Promote Node to Master**
>
> `curl -X POST http://localhost:8777/promote -H "Content-Type: application/json" -d "{\"role\": \"master\", \"ip\": \"192.168.0.12\"}"`
> 
> This triggers the backend node to:
> * Promote itself to master 
> * Start sending heartbeats 
> * Start serving state via TCP

### Backend → Frontend
> 1. When a node is promoted to master, it sends a simple HTTP request to the frontend to update the UI state:
> 
>   `curl -X POST http://localhost:8778/updateRole -H "Content-Type: application/json" -d "{\"role\": \"master\", \"ip\": \"192.168.0.12\"}"`
>
> 2. Similarly, when demoted, it sends:
> 
>   `curl -X POST http://localhost:8778/updateRole -H "Content-Type: application/json" -d "{\"role\": \"slave\", \"ip\": \"192.168.0.12\"}"`
>
> This allows the frontend to visually reflect real-time leadership status.
> * Promote itself to master 
> * Start sending heartbeats 
> * Start serving state via TCP

## JSON Objects Used

> #### ServersData
> 
> `{
  "lastUpdate": 1706515614,
  "serversList": [
    {
      "host": "server-01",
      "app": "Mid",
      "ip": "192.168.0.10",
      "env": "preprod",
      "available": true,
      "action": "Available",
      "since": 0,
      "comment": ""
    }
  ]
}`

> #### ClusterView
> 
> `[
  { "nodeIP": "192.168.1.10", "role": "master" },
  { "nodeIP": "192.168.1.11", "role": "slave" }
]`

> #### UserRequests
> 
> `[
  {
    "nodeIP": "192.168.1.11",
    "timestamp": 1706515614,
    "operation": "reserve",
    "serverHost": "server-01",
    "comment": "integration tests"
  }
]`