// import { head, post } from "aws-amplify/api";
// import { API_NAME } from "../constants";
import { ApiClientBase } from "./api-client-base";
import { Amplify } from "aws-amplify";
import { fetchAuthSession } from "aws-amplify/auth";

export class TickerNewsApiClient extends ApiClientBase {
  cnf = Amplify.getConfig() ;
  //wssUrl = this.cnf?.API?.REST?.WebSocketApi?.endpoint;
  wssUrl = "" ;

  ws = new WebSocket("wss://el9i3t0te8.execute-api.us-east-1.amazonaws.com/prod/");

  constructor() {
    super() ;
    this.getIdToken().then((value)=> {
      console.log(value)
      this.wssUrl = `wss://el9i3t0te8.execute-api.us-east-1.amazonaws.com/prod/?idToken=${value}`;
      this.ws = new WebSocket(this.wssUrl);
      // Connection opened
      this.ws.addEventListener("open", event => {
        this.ws.send("Connection established" + event)
      });

      // Listen for messages
      this.ws.addEventListener("message", event => {
        console.log("Message from server ", event.data)
      });
    }) ;
  }


  async news(message:string): Promise<any> {
    //const headers = await this.getHeaders();
    // const restOperation = post({
    //   apiName: API_NAME,
    //   path: "/tickernews",
    //   options: {
    //     headers,
    //     body:{
    //       message: message
    //     }
    //   },
    // });

    // const response = await restOperation.response;
    // const data = (await response.body.json()) as any;

    // return data;

    console.log(this.wssUrl + ":" + message);
    this.ws.send(
      JSON.stringify({
        action: "sendmessage",
        data: message,
      })
    );

    return null;
  }
  
  protected async getIdToken() {
    const session = await fetchAuthSession();
    return session.tokens?.idToken?.toString();
  }

}
