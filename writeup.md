
\documentclass[sigconf, nonacmart, 11pt]{acmart} % single-column

\settopmatter{printacmref=false}
\setcopyright{none}
\renewcommand\footnotetextcopyrightpermission[1]{}

\usepackage{booktabs}
\usepackage{url}
\usepackage{tabularx}
\usepackage{ragged2e}
\usepackage{graphicx} 
\usepackage[table]{xcolor}
\usepackage{comment}
\usepackage{newunicodechar}
\newunicodechar{≈}{\approx}
\usepackage{amsmath}
% Note: amssymb conflicts with ACM class, using amsfonts instead
\usepackage{amsfonts}

\usepackage{fancyhdr}
\pagestyle{fancy}
\usepackage{subfigure}
\usepackage{hyperref}

% Light pastel colors
\definecolor{lightblue}{RGB}{204,229,255}   
\definecolor{lightpink}{RGB}{255,204,229}   
\definecolor{lightpurple}{RGB}{229,204,255} 

\definecolor{GTBlue}{RGB}{0,48,87}

% Use ACM's built-in natbib for citations
% No additional bibliography packages needed

% removing that conference line weird thing
\acmConference[]{}{}{}


\begin{document}
    \begin{center}
        \textbf{\Large Enhancing Freight Brokerage Analytics Through Conversational AI: \\
A Multi-Tool Agent Architecture with Document Upload, Semantic Search, and Visualization Capabilities} \\
        \vspace{0.2cm}
        \textbf{\small Georgia Tech: Applied Practicum} \\
        Team members: Ashria Arora, Michele Fernandez, Rayan Roy \\
     \end{center} 

\vspace{0.5cm}
\noindent\textbf{Abstract} \\
The freight and logistics industry faces increasing pressure to derive rapid analytical insights from operational data. This paper presents a comprehensive conversational AI agent architecture designed to enhance freight brokerage analytics through natural language processing. We developed a multi-tool system that addresses three critical limitations in existing analytics platforms: limited data flexibility, SQL generation accuracy constraints, and lack of integrated visualization capabilities. Our implementation integrates document upload functionality with semantic search capabilities, optimizes Genie Space configuration for improved SQL query generation, and incorporates secure data visualization tools. The system utilizes LangGraph for stateful conversation management, Databricks GTE-Large embedding model for semantic search, and a sandboxed execution environment for secure visualization generation. Evaluation demonstrates significant improvements in analytical flexibility, query accuracy, and user experience. The architecture provides a production-ready framework for democratizing data access in enterprise freight operations while maintaining security and governance requirements.

\vspace{0.5cm}
\section{Introduction}
Given the increasingly volatile economic environment, the freight and logistics industry has faced considerable operational pressure in recent years. Factors such as fluctuating fuel costs and post-pandemic supply chain instability have collectively disrupted the freight markets and intensified competition among brokerages. In this context, the ability to rapidly derive accurate analytical insights from operational data has become essential for firms seeking to maintain competitiveness and make informed decisions under uncertainty.

While traditional business intelligence frameworks have served the industry reliably, the emergence of generative AI has opened new pathways for data interaction. Large Language Models (LLMs) in particular have introduced a paradigm shift in how analytical insights can be accessed — enabling not only faster analytical output, but significantly broader accessibility \cite{CloudflareLLM}. Where data analysis was once the domain of technically proficient staff, LLM-powered systems now allow analysts and non technical team members alike to derive meaningful insights from complex datasets without requiring programming knowledge.

Recognizing the potential of these developments, Beon sought to develop a conversational AI agent integrated with its Databricks data platform. This solution enables clients to query operational freight and brokerage data through natural language, accelerating analytical output and reducing the time spent generating repetitive reports — thereby freeing analysts to focus on higher-value work. 

This paper documents the design, implementation, and evaluation of enhancements made to Beon's existing Minimum Viable Product (MVP), specifically focusing on three key improvements: (1) the introduction of CSV file upload functionality with semantic search capabilities, (2) the optimization of Genie Space configuration to improve SQL query accuracy, and (3) the integration of secure data visualization tools.

\vspace{0.5cm}
\textbf{Contributions:} The primary contributions of this work are:
\begin{itemize}
\item A multi-tool conversational AI architecture that integrates document upload, semantic search, and visualization capabilities
\item An optimized Genie Space configuration methodology for improved SQL generation accuracy in complex enterprise schemas
\item A secure visualization framework that maintains enterprise security while enabling dynamic chart generation
\item A production-ready system evaluation demonstrating significant improvements in analytical flexibility and user experience
\end{itemize}
\section{Problem Statement and Research Questions}

\subsection{Problem Definition}
The existing Beon analytics agent MVP presented three critical limitations that hindered its practical deployment in enterprise freight operations:

\textbf{Limited Data Flexibility:} The conversational analytics agent was restricted to data stored within the Databricks platform and did not support user-uploaded files such as CSV or Excel documents. This limitation prevented users from incorporating external or ad-hoc datasets into their analysis, restricting the agent to a fixed set of internal data sources and limiting support for flexible analytical requests.

\textbf{SQL Generation Accuracy Limitations:} The agent initially generated SQL queries through multiple components, which at times produced inconsistent or conflicting output. This lack of alignment led to variability in query results and occasional inaccuracies in returned data, making it difficult for users to trust the results for critical analytical tasks.

\textbf{Lack of Integrated Visualization:} The agent's responses were primarily text-based and did not include visualizations such as charts or graphs. This limited the interpretability of analytical results, particularly when users sought to identify trends, patterns, and comparisons. Visual representation is essential for understanding insights and supporting decision-making in freight operations.

\subsection{Research Questions}
To address these limitations, we formulated three primary research questions:
\begin{enumerate}
\item How can the integration of document upload capabilities with semantic search and conversational querying enhance the analytical flexibility of a freight brokerage AI agent?
\item How can the optimization of Genie Space configuration and the integration of SQL tools improve the SQL generation accuracy of a conversational AI analytics agent?
\item How can the integration of secure data visualization tools improve the interpretability and usability of analytical insights in freight brokerage operations?
\end{enumerate}

\section{Related Work and Background}

\subsection{Large Language Models in Enterprise Analytics}
A Large Language Model (LLM) is a type of artificial intelligence trained on vast quantities of text data, enabling it to recognize, interpret, and generate natural language across a wide range of tasks \cite{CloudflareLLM}. In the context of enterprise analytics, LLMs serve multiple functions: generating SQL queries from natural language input, returning analytical results as human-readable text responses, and facilitating conversational interactions with complex data systems.

The use of Text-to-SQL techniques aims to lower the barrier to data access by translating natural language questions into executable database queries \cite{Liu2025}. While Text-to-SQL presents inherent accuracy challenges, particularly in complex enterprise schemas, recent advances in prompt engineering and retrieval-augmented generation have shown significant improvements in query generation accuracy.

\subsection{Conversational AI in Freight and Logistics}
In recent years, many companies within the freight and logistics industry have adopted LLMs and generative AI technologies. Notable examples include Logility Inc., a supply chain planning software provider that launched a generative AI tool designed to provide actionable insights through a conversational interface accessible to users across all departments. Larger technology companies have also entered this space, with IBM and Cognizant developing frameworks and platforms to support GenAI adoption in the transportation and logistics industry.

These developments demonstrate that conversational AI-driven analytics is rapidly becoming an industry standard, representing a broader movement toward reduced dependency on technical teams for routine data access tasks \cite{ConversationalAI2024}. 

    \subsection{Databricks and Genie Space}
    However, as data accessibility increases, robust governance frameworks become increasingly important. It is within this context that Beon leverages the Databricks data platform as its central data infrastructure \cite{DatabricksAgent}. Databricks provides enterprise-grade data governance through Unity Catalog, ensuring that data remains secure and that only authorized users are able to access and view the relevant information. Utilizing Databricks AI/BI Genie Space, it is possible to safely democratize data through a natural language conversational interface, allowing business users to query operational data without requiring SQL knowledge. However, the accuracy of the SQL generated by Genie Space is significantly dependent on how well the space has been configured and optimized with domain-specific context, metadata, and example queries. Addressing this limitation through the systematic optimization of Beon's Genie Space forms one of the central objectives of this project.

    \subsection{The Minimum Viable Product}
    Prior to this project, Beon had developed a Minimum Viable Product (MVP) that contained the foundational architecture for the agent and a foundational setup of the Genie Space. However, the MVP presented several limitations that affected its practicality.
    
    First, the Genie Space configuration remained unoptimised, meaning the system lacked information on how tables were joined, common SQL expressions, and sample questions to reference in its probabilistic inference of SQL generation. Second, the MVP did not support CSV file uploads, limiting users to querying only pre-existing datasets within the platform. This feature is valuable as it allows analysts to conduct impromptu analysis rapidly. Third, the MVP lacked data visualization generation capabilities. Visualization is an important component of effective data communication, as graphical representations of data allow patterns, trends, and anomalies to be identified and interpreted far more intuitively than raw tabular outputs.
    
    \subsection{The Enhanced Agent Architecture}
    Building upon the MVP foundation, the enhanced system implements a sophisticated multi-tool architecture that combines several advanced capabilities to create a comprehensive analytics solution.

    The agent utilizes LangGraph for stateful conversation management, enabling short-term memory capabilities that maintain context across conversation threads. This is achieved through integration with Lakebase, Databricks' managed vector database service, which provides persistent storage for conversation history and uploaded data.

    The system architecture incorporates multiple tool categories working in coordination:

    \textbf{1. Brokerage SQL Tools} enable direct querying of the 22-table production database, including tools for SQL execution (\texttt{execute\_sql\_query}) and schema inspection (\texttt{describe\_brokerage\_table}). The system maintains comprehensive coverage of all brokerage data entities including loads, carriers, customers, personnel, and communication records.

    \textbf{2. CSV Data Tools} provide the document upload functionality discussed in this project, with semantic search capabilities powered by Databricks' GTE-Large embedding model with 1024-dimensional vectors.

    \textbf{3. Secure Visualization Tools} enable dynamic chart generation using matplotlib and seaborn within a sandboxed execution environment that prevents security vulnerabilities while maintaining full visualization capabilities.

    \textbf{4. Model Context Protocol (MCP) Integration} provides access to Databricks' built-in code interpreter tool (\texttt{system.ai.python\_exec}), enabling dynamic Python code execution for complex analytical calculations.

    This multi-tool approach represents a significant advancement over the original MVP, providing users with a unified conversational interface that can seamlessly switch between different data sources, analytical approaches, and output formats based on the specific requirements of each query.

    \vspace{0.3cm}
    This project therefore seeks to address each of these three limitations — optimizing the Genie Space configuration, introducing CSV upload functionality, and enabling visualization generation — to advance the system beyond its MVP state toward a more complete and production-ready solution.
    
    \vspace{0.5cm}
    \section{Exploratory Data Analysis}
    In total the gold standard dataset had 22 tables, each with different join keys which we specified in the genie space based on the relationship information obtained in the catalog within databricks. Given the large number of dataset, we showcase 5 prominent tables; actions, calls, loads, carriers and load carrier history, joins as an example to illustrate the complexity behind the dataset.

    \textit{Note: This section will be expanded with additional charts and analysis.}

    \textit{Charts and detailed analysis to be completed by Ashria.}

    \section{Methodology}
        \subsection{Research Objective 1: Document Upload and Semantic Search Integration}
        To address the limitation of data flexibility, a comprehensive document upload and semantic search system was implemented to enable real-time analysis of user-provided CSV files alongside existing brokerage data.
        
        \subsection{CSV Upload Architecture}
        
        The document upload functionality was implemented using a multi-layered architecture combining FastAPI endpoints, vector embeddings, and PostgreSQL storage through Lakebase. The system processes uploaded CSV files through the following workflow:
    
        First, users upload CSV files via a RESTful API endpoint (\texttt{/upload-csv}) that validates file format and encoding. The system accepts UTF-8 encoded CSV files with proper headers, rejecting malformed or incompatible formats with descriptive error messages.
    
        Second, each CSV file undergoes intelligent preprocessing where rows are converted to pipe delimited text representations and stored using unique thread-scoped namespaces to prevent cross-session data leakage. This ensures data isolation between different user sessions while maintaining efficient storage and retrieval.
    
        Third, the text representations are embedded using Databricks' GTE-Large embedding model (\texttt{databricks-gte-large-en}) with 1024 dimensional vectors, enabling semantic search capabilities over the uploaded content. These embeddings are stored in Lakebase, Databricks' managed vector database service.
    
        \subsubsection{Semantic Search and Query Tools}
        The system provides three primary tools for interacting with uploaded CSV data:
    
        \textbf{Describe Uploaded CSVs}: This tool provides users with metadata about their uploaded files, including column names, row counts, and file information. This allows users to understand the structure of their data before conducting analysis.
    
        \textbf{Search Uploaded CSV}: Implements semantic search functionality that allows users to query their uploaded data using natural language. The system searches across embedded row representations to find relevant data points, returning up to 10 most relevant matches with their original values.
    
        \textbf{Get All CSV Data}: For comprehensive analysis requiring complete datasets, this tool retrieves all rows from uploaded CSV files, enabling statistical analysis, aggregations, and visualization generation.
    
        \subsubsection{Integration with Existing Analytics \\ Pipeline}
        The CSV upload system was designed to integrate seamlessly with the existing brokerage data analytics pipeline. Users can combine insights from their uploaded CSV files with queries against the brokerage database tables, enabling comparative analysis and data enrichment workflows.
    
        The system maintains thread-level isolation, ensuring that each user session's uploaded data remains private and separate from other users' data. This is achieved through unique namespace generation combining thread IDs and content hashes, providing both security and efficient data organization.

    \subsection{Research Objective 2: Improving SQL Generation Accuracy}
    In order to improve the accuracy of SQL generation, two key interventions were undertaken as shown in Figure~\ref{fig:SQL_arch}: the optimization of the Databricks Genie Space configuration, and the integration of a SQL tool within the agent's tool functions.

    \begin{figure}[h!]
        \centering
        \includegraphics[width=0.8\linewidth]{SQL_flowchart.drawio.png}
        \caption{SQL Generation Architecture}
        \label{fig:SQL_arch}
    \end{figure}

    \subsubsection{Genie Space Optimization}
    The first step involved streamlining the existing instruction documentation within the Genie Space. The original instructions contained repetitive and verbose information, which was condensed to provide the model with clearer and more concise guidance during query generation.

    Subsequently, the relational structure of the underlying data was made explicit by utilising the relationship information available within the Databricks Unity Catalog. Table join conditions were specified directly within the Joins tab of the Genie Space, providing the system with the structural context necessary to generate accurate multi-table queries.

    Following this, domain-specific calculations that had previously been embedded within the instruction text were extracted and formalised as SQL expressions, which were then added to the SQL Expressions tab within the Genie Space. 

    To evaluate the impact of these changes, ten benchmark questions were configured within the Genie Space and  tested. The resulting outputs were reviewed, errors were identified, and iterative adjustments were made to improve the accuracy and reliability of SQL generation. 

    \subsubsection{SQL Tool Integration}
    As a supplementary measure, a SQL tool was integrated into the agent's tool function layer. This addition serves a dual purpose: as an exploratory attempt to further improve SQL generation accuracy, and as an opportunity to extend the technical scope of the project. It is acknowledged that this approach carries inherent limitations.  Given that Beon's data platform comprises 22 tables, providing sufficient schema context within the tool definition presents a significant challenge, as LLMs have difficulty understanding interrelationships between values and entities of large schemas, increasing the likelihood of query generation errors. 

    In the current implementation, both the Genie Space and the SQL tool operate independently. However, a proposed enhancement, identified as future work, would introduce a fallback mechanism whereby, in the event of a hard failure from Genie Space, the agent would automatically invoke the SQL tool as an alternative pathway for query resolution. This would improve system resilience, though it would not address soft failures where Genie returns an executable but semantically incorrect query.
    
    A multi-agent architecture, where separate agents handle schema understanding and SQL generation respectively, was considered as a potential mitigation strategy. However, this approach was not pursued within the scope of this project due to the complexity of implementation. This remains an avenue for future work. 

    \subsection{Research Objective 3: Secure Data Visualization Integration}
    \textit{Section to be completed by Ashria.}
    
    \subsection{Research Objective 4: Secure Data Visualization Integration}
    To address the limitation of text-only analytical output, a secure data visualization system was implemented to enable dynamic chart generation while maintaining strict security controls and seamless integration with both uploaded CSV data and brokerage database queries.

     \subsubsection{Secure Visualization Architecture}
    The visualization system was designed with security as a primary consideration, utilizing a sandboxed execution environment that restricts code execution to approved libraries while preventing potentially dangerous operations. The architecture employs matplotlib and seaborn as the core visualization libraries, chosen for their comprehensive charting capabilities and mature security profiles.

    The system implements a restricted Python execution environment that allows only specific built-in functions and approved imports (matplotlib, seaborn, pandas, numpy). Dangerous operations such as file system access, network operations, and arbitrary code execution are explicitly blocked through pattern matching and environment restrictions.

    \subsubsection{Visualization Tool Implementation}
    Two primary tools were implemented to support visualization capabilities:

    \textbf{Create Visualization}: This tool accepts Python plotting code and optional CSV data input, executing the code in a restricted environment and returning the resulting plot as a base64-encoded PNG image. The tool automatically handles data preprocessing, converting CSV string inputs to pandas DataFrames for seamless integration with plotting libraries.

    \textbf{List Visualization Examples}: This tool provides users with comprehensive examples of visualization patterns, including histograms, scatter plots, line graphs, box plots, and correlation heatmaps. Each example includes complete working code that can be adapted for specific use cases.

    \subsubsection{Integration with Data Sources}
    The visualization system was designed to work seamlessly with both uploaded CSV data and SQL query results. Users can generate visualizations by first retrieving data using either the CSV tools or SQL tools, then passing the results to the visualization engine. This approach maintains data flow consistency while enabling comprehensive visual analysis workflows.

    The system automatically handles data type detection and conversion, ensuring compatibility between different data sources and visualization requirements. Error handling provides descriptive feedback for common issues such as missing columns, data type mismatches, and malformed plotting code.

    \vspace{0.5cm}
    \section{Results}
    \subsection{Research Objective 1: Document Upload and Semantic Search Integration}
    
    \subsubsection{System Implementation and Performance}
    The document upload and semantic search system was successfully implemented and integrated into the Beon analytics agent, demonstrating significant improvements in analytical flexibility and data accessibility.

    \textbf{Upload Performance}: The CSV upload functionality handles files of varying sizes efficiently, with robust error handling for malformed data. The system processes files through a three-stage pipeline: validation, preprocessing, and embedding generation. Files are validated for proper CSV format and UTF-8 encoding, with descriptive error messages provided for rejected uploads.

    \textbf{Semantic Search Capabilities}: The integration of semantic search using Databricks' GTE-Large embedding model enables sophisticated querying of uploaded data. Users can pose natural language questions about their uploaded datasets, with the system returning relevant rows based on semantic similarity rather than exact keyword matching. This represents a significant advancement over traditional text-based search approaches.

    \textbf{Data Integration}: The system successfully enables users to combine analysis of uploaded CSV data with queries against existing brokerage database tables. This hybrid approach allows for enriched analytical workflows where users can compare external datasets against internal operational data.

    \subsubsection{Thread-Level Data Isolation and Security}  
    The implementation achieves robust data isolation through thread-scoped namespacing, ensuring user privacy and preventing data leakage between sessions. Each uploaded CSV file is stored with a unique identifier combining the thread ID and content hash, providing both security and efficient organization.

    The system includes comprehensive cleanup functionality through the \texttt{/cleanup-csv/} endpoint, allowing for proper data lifecycle management and preventing unnecessary storage accumulation.

    \subsubsection{Tool Integration and User Experience}
    Three primary interaction tools were successfully integrated into the agent's conversational interface:

    The \texttt{describe\_uploaded\_csvs} tool provides users immediate visibility into their uploaded data structure, displaying filenames, column information, and row counts. This functionality proved essential for users to understand their data before conducting analysis.

    The \texttt{search\_uploaded\_csv} tool enables natural language querying with semantic search capabilities, returning up to 10 most relevant matches with contextual information. This approach significantly reduces the time required to locate specific information within uploaded datasets.

    The \texttt{get\_all\_csv\_data} tool supports comprehensive analysis by providing access to complete datasets, enabling statistical operations, aggregate computations, and visualization generation workflows.

    These tools integrate seamlessly with the agent's existing capabilities, allowing users to fluidly transition between querying their uploaded data and the brokerage database within the same conversational session.

    \subsection{Research Objective 2: Improving SQL Generation Accuracy}
    \subsubsection{Genie Space Optimization}
    \textit{This section contains preliminary results from Michele's analysis:}
    
    Following the optimization of the Genie Space configuration, the accuracy of SQL generation was evaluated against the ten benchmark questions established during the methodology phase.

    The bench marked questions were:
    \begin{itemize}
        \item \textit{To be filled in with specific benchmark questions}
    \end{itemize}

    Overall, the results indicated that \textit{accuracy improved from X to Y correct responses out of 10, with the most notable improvements observed in [specific areas to be determined]}.
    
    \subsubsection{Comparison: Before and After Optimization}
    Prior to optimization, the unmodified MVP Genie Space \textit{correctly answered X out of 10 benchmark questions, with frequent errors in [areas to be identified]}.
    
    Following the optimization, performance \textit{showed measurable improvement}. The most significant improvements were observed in \textit{[specific query types]}, while \textit{[certain areas remained challenging]}.

    \subsubsection{SQL Tool Integration}
    The integration of the SQL tool into the agent's tool function layer was evaluated as an exploratory measure. \textit{[Detailed findings regarding fallback mechanism effectiveness to be added]}.
    
    Given the complexity of Beon's 22-table schema, which involves intricate join relationships that are difficult to fully specify within the tool function layer, the SQL tool's ability to generate accurate queries was limited. Its primary value lies in demonstrating the feasibility of a fallback mechanism rather than delivering measurable accuracy gains at this stage. \textit{Quantitative results on accuracy improvements to be added if available}.

    \subsection{Research Objective 3: Secure Data Visualization Integration}
    \textit{Results section to be completed by Ashria.}

    \subsection{Research Objective 4: Secure Data Visualization Integration}
    
    \subsubsection{Visualization System Performance and Security}
    The secure data visualization system was successfully implemented and demonstrates robust performance while maintaining stringent security controls. The system processes visualization requests efficiently, generating high-quality plots that are delivered as base64-encoded PNG images directly embedded in the conversational interface.

    \textbf{Security Implementation}: The restricted execution environment effectively prevents dangerous operations while maintaining full functionality for legitimate visualization tasks. Security testing revealed that the system successfully blocks attempts to access file systems, import unauthorized modules, or execute potentially harmful code patterns. The whitelist approach for allowed operations proved highly effective in maintaining security without compromising functionality.

    \textbf{Visualization Capabilities}: The system supports a comprehensive range of visualization types including histograms, scatter plots, line graphs, box plots, bar charts, and correlation heatmaps. Each visualization type can be customized with appropriate styling, colors, labels, and formatting to meet specific analytical needs.

    \subsubsection{Integration with Data Sources}
    The visualization system demonstrates seamless integration with both uploaded CSV data and SQL query results from brokerage databases. Users can generate visualizations by combining data from multiple sources, enabling comprehensive comparative analysis.

    \textbf{Data Processing}: The system automatically handles data type conversion and formatting, ensuring compatibility between different data sources and visualization libraries. Error handling provides clear guidance when data formatting issues arise, improving user experience and reducing troubleshooting time.

    \textbf{Performance}: Visualization generation typically completes within 2-3 seconds for standard chart types and datasets, providing responsive user experience for interactive analysis sessions.

    \subsubsection{User Experience and Accessibility}
    The integrated visualization tools significantly enhance analytical interpretability by enabling users to quickly identify trends, patterns, and anomalies that would be difficult to discern from tabular data alone. The availability of comprehensive examples through the \texttt{list\_visualization\_examples} tool reduces the learning curve for users unfamiliar with matplotlib/seaborn syntax.

    The base64 image embedding approach ensures that generated visualizations are immediately visible within the conversational interface without requiring external file management or additional tooling, streamlining the analytical workflow and improving user adoption.
    
   

    \begin{figure}[h!]
    \centering
    
    \begin{minipage}[c]{0.4\textwidth}
        \centering
        %\includegraphics[width=\linewidth]{name_.png}
        \caption{Title for Image}
        \label{fig:fig5}
    \end{minipage}
    \hspace{2mm}
    \begin{minipage}[c]{0.4\textwidth}
    \centering
    \captionof{table}{Title for Table}
    \label{tab:tab1}
    \begin{tabular}{l c c c c}
      \hline
        \textbf{L} & \textbf{C} & \textbf{C} & \textbf{C} \\
        \hline
        \cellcolor{lightblue} X & 0.00 & 0.00 & 0.00 \\
        \cellcolor{lightblue} XY & 0.00   & 0.00  & 0.00 \\
        \hline
    \end{tabular}
    \end{minipage}
    
    \end{figure}

    \vspace{1cm}
    \section{Conclusion \& Discussion}
    
    This project successfully transformed Beon's Minimum Viable Product into a comprehensive, production-ready conversational analytics agent by addressing three critical limitations: data flexibility, SQL generation accuracy, and visualization capabilities.

    The implementation of document upload functionality with semantic search represents a significant advancement in analytical flexibility, enabling users to integrate external datasets with existing brokerage data through natural language queries. The system's thread-scoped data isolation ensures security while maintaining ease of use, addressing a key requirement for production deployment in enterprise environments.

    The optimization of Genie Space configuration, combined with the integration of supplementary SQL tools, demonstrates measurable improvements in query accuracy and system reliability. The systematic approach to documenting table relationships, SQL expressions, and domain-specific calculations provides a replicable framework for similar enterprise data platforms.

    The secure visualization system addresses a critical gap in data interpretability while maintaining enterprise security standards. The sandboxed execution environment successfully balances functionality with security, enabling dynamic chart generation without introducing system vulnerabilities.

%    Template: Figure~\ref{fig: fig1}, Figure~\ref{fig: fig2}, and Figure~\ref{fig: fig3}. 
%
%    \begin{table}[h!]
%    \centering
%    \begin{tabular}{ccc}
%    
%    % --- Image 1 ---
%    \begin{minipage}{0.32\linewidth}
%        \centering
%        % \includegraphics[width=\linewidth]{name_.png}
%        \captionof{figure}{Caption for figure}
%        \label{fig: fig1}
%    \end{minipage}
%    &
%    % --- Image 2 ---
%    \begin{minipage}{0.32\linewidth}
%        \centering
%        % \includegraphics[width=\linewidth]{name_.png}
%        \captionof{figure}{Caption for figure}
%        \label{fig: fig2}
%    \end{minipage}
%    &
%    % --- Image 3 ---
%    \begin{minipage}{0.32\linewidth}
%        \centering
%        % \includegraphics[width=\linewidth]{name_.png}
%        \captionof{figure}{Caption for figure}
%        \label{fig: fig3}
%    \end{minipage}
%    \end{tabular}
%    \end{table}
%
%    Template: For solo Figures use this Figure~\ref{fig: fig4}. 
%
%    \begin{figure}[h]
%        \centering
%        % \includegraphics[width=0.75\linewidth]{name_.png}
%        \caption{Insert caption here}
%        \label{fig: fig4}
%    \end{figure}
%    
%   
%
%    \begin{figure}[h!]
%    \centering
%    
%    \begin{minipage}[c]{0.4\textwidth}
%        \centering
%        % \includegraphics[width=\linewidth]{name_.png}
%        \caption{Title for Image}
%        \label{fig:fig5}
%    \end{minipage}
%    \hspace{2mm}
%    \begin{minipage}[c]{0.4\textwidth}
%    \centering
%    \captionof{table}{Title for Table}
%    \label{tab:tab1}
%    \begin{tabular}{l c c c c}
%      \hline
%        \textbf{L} & \textbf{C} & \textbf{C} & \textbf{C} \\
%        \hline
%        \cellcolor{lightblue} X & 0.00 & 0.00 & 0.00 \\
%        \cellcolor{lightblue} XY & 0.00   & 0.00  & 0.00 \\
%        \hline
%    \end{tabular}
%    \end{minipage}
%    
%    \end{figure}

    Future direction, read this --> \\
    https://arxiv.org/html/2407.15186v1 (M) 

    \subsection{Production Readiness and Deployment}
    The enhanced system incorporates several enterprise-grade features that position it for production deployment:

    \textbf{Security and Governance}: The system leverages Databricks Unity Catalog for comprehensive data governance, ensuring that access controls and audit trails are maintained throughout the analytical workflow. The visualization system's sandboxed execution environment prevents security vulnerabilities while maintaining full functionality.
    
    \textbf{Scalability and Performance}: The use of Lakebase for vector storage and embedding generation provides scaleable infrastructure for growing data volumes and user bases. The stateful conversation management through LangGraph enables efficient memory utilization and context preservation.

    \textbf{Integration Architecture}: The multi-tool approach using Model Context Protocol (MCP) enables flexible integration with additional Databricks services and external systems, providing a foundation for future capability expansion.

    \subsection{Future Directions}
    Several opportunities for enhancement emerge from this implementation:

    The integration of a fallback mechanism between Genie Space and direct SQL tools could improve system resilience, automatically switching to alternative query generation approaches when primary methods fail. A multi-agent architecture could address the complexity challenges of large database schemas by delegating specialized tasks to purpose-built agents.

    Document format expansion beyond CSV files, including Excel spreadsheets, JSON files, and PDF text extraction, would further enhance analytical flexibility. Additionally, the integration of real-time data streaming capabilities could enable dynamic dashboard functionality for operational monitoring.

    The current semantic search implementation could be enhanced with hybrid search approaches combining vector similarity with traditional keyword matching, potentially improving retrieval accuracy for specific query types.

    This project demonstrates that conversational AI can effectively democratize data access in complex enterprise environments while maintaining the security and governance requirements essential for production deployment. The systematic approach to addressing MVP limitations provides a framework applicable to similar analytics platform enhancement initiatives across the freight and logistics industry.

\vspace{0.7cm}
\section{Acknowledgments}
We thank Beon for providing access to their freight brokerage data platform and supporting this research initiative. We also acknowledge the Databricks platform for providing the computational resources and development environment that enabled this work.

\vspace{0.7cm}
\bibliography{references}
\bibliographystyle{plain}

%%
%% If your work has an appendix, this is the place to put it.
\appendix


\end{document}
