
import Container from "@cloudscape-design/components/container";
import Header from "@cloudscape-design/components/header";
import { TextContent } from "@cloudscape-design/components";

export default function ClaimsProcessingHomePage() {
    return (
            <Container
                header={
                <Header
                    variant="h2"
                    description="Guidance Package for Omnichannel Claims Processing Powered by Generative AI on AWS: This package offers instructions for implementing Generative AI-powered Omnichannel Claims Processing using Amazon Bedrock and AWS customer experience services, including Amazon Connect, Lex, and Pinpoint. It focuses on streamlining auto insurance claims handling to improve customer experience and enhance processing efficiency."
                >
                    Overview
                </Header>
                }
            >
                <TextContent>
                    <p>
                        <h3>Key Features</h3>
                        
                    </p>
                    <ul>
                        <li> Step-by-step implementation guide for First Notice of Loss (FNOL) solution </li>  
                        <li> Integration with Amazon Bedrock for advanced AI capabilities </li>  
                        <li> Automated claims management process </li>  
                        <li> Fraud detection and prevention mechanisms </li>                   
                    </ul>
                    <p>
                        <h3> Benefits</h3>
                    </p>
                    <ul>
                        <li> Personalized Omnichannel customer engagement </li>  
                        <li> Increased accuracy in claims processing </li>  
                        <li> Enhanced efficiency in claims handling </li>  
                        <li> Improved fraud prevention </li>   
                        <li> Reduced processing times </li>   
                        <li> Improved customer experience</li>   
                    </ul>
            </TextContent>
            </Container>
 )
}
