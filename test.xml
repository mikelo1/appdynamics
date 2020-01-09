<root>
    <health-rule>
        <name>HR_LOGIN</name>
        <type>BUSINESS_TRANSACTION</type>
        <description/>
        <enabled>true</enabled>
        <is-default>false</is-default>
        <always-enabled>false</always-enabled>
        <duration-min>10</duration-min>
        <wait-time-min>30</wait-time-min>
        <schedule>Rsi 23-24h</schedule>
        <affected-entities-match-criteria>
            <affected-bt-match-criteria>
                <type>SPECIFIC</type>
                <business-transactions>
                    <business-transaction application-component="APIManager">Login</business-transaction>
                </business-transactions>
            </affected-bt-match-criteria>
        </affected-entities-match-criteria>
        <critical-execution-criteria>
            <entity-aggregation-scope>
                <type>ANY</type>
                <value>0</value>
            </entity-aggregation-scope>
            <policy-condition>
                <type>leaf</type>
                <display-name>TasaError</display-name>
                <condition-value-type>BASELINE_STANDARD_DEVIATION</condition-value-type>
                <condition-value>6.0</condition-value>
                <operator>GREATER_THAN</operator>
                <condition-expression/>
                <use-active-baseline>true</use-active-baseline>
                <trigger-on-no-data>false</trigger-on-no-data>
                <enable-triggers>false</enable-triggers>
                <min-triggers>0</min-triggers>
                <metric-expression>
                    <type>leaf</type>
                    <function-type>VALUE</function-type>
                    <value>0</value>
                    <is-literal-expression>false</is-literal-expression>
                    <display-name>null</display-name>
                    <metric-definition>
                        <type>LOGICAL_METRIC</type>
                        <logical-metric-name>Errors per Minute</logical-metric-name>
                    </metric-definition>
                </metric-expression>
            </policy-condition>
        </critical-execution-criteria>
        <warning-execution-criteria>
            <entity-aggregation-scope>
                <type>ANY</type>
                <value>0</value>
            </entity-aggregation-scope>
            <policy-condition>
                <type>leaf</type>
                <display-name>TasaError</display-name>
                <condition-value-type>BASELINE_STANDARD_DEVIATION</condition-value-type>
                <condition-value>4.0</condition-value>
                <operator>GREATER_THAN</operator>
                <condition-expression/>
                <use-active-baseline>true</use-active-baseline>
                <trigger-on-no-data>false</trigger-on-no-data>
                <enable-triggers>false</enable-triggers>
                <min-triggers>0</min-triggers>
                <metric-expression>
                    <type>leaf</type>
                    <function-type>VALUE</function-type>
                    <value>0</value>
                    <is-literal-expression>false</is-literal-expression>
                    <display-name>null</display-name>
                    <metric-definition>
                        <type>LOGICAL_METRIC</type>
                        <logical-metric-name>Errors per Minute</logical-metric-name>
                    </metric-definition>
                </metric-expression>
            </policy-condition>
        </warning-execution-criteria>
    </health-rule>
    <scope-list>
         <scope scope-description="" scope-name="Default Scope"
            scope-type="ALL_TIERS_IN_APP" scope-version="3"/>
    </scope-list>
    <rule-list>
        <rule agent-type="APPLICATION_SERVER" enabled="true"
            priority="100"
            rule-description="Refresco de token de autenticacion."
            rule-name="Refresh_token_onetime" rule-type="TX_MATCH_RULE" version="2">
            <tx-match-rule>{"type":"CUSTOM","txcustomrule":{"type":"INCLUDE","txentrypointtype":"SERVLET","matchconditions":[{"type":"HTTP","httpmatch":{"uri":{"type":"EQUALS","matchstrings":["/fullonline/refresh_token"]},"parameters":[],"headers":[],"cookies":[]}}],"actions":[],"properties":[]},"agenttype":"APPLICATION_SERVER"}</tx-match-rule>
        </rule>
    </rule-list>
    <scope-rule-mapping-list>
        <scope-rule-mapping scope-name="Default Scope">
            <rule
                rule-description="Refresco de token de autenticacion." rule-name="Refresh_token_onetime"/>
        </scope-rule-mapping>
    </scope-rule-mapping-list>
</root>