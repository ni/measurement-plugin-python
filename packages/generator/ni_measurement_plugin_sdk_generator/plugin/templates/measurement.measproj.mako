<%page args="ui_file"/>\
\
<?xml version="1.0" encoding="utf-8"?>
<SourceFile Checksum="45C379C12E21531099FA05BA0133A871C1484C2D21AE60D19E992798D99A4020F84B7105887E5560BD63521128915683E687C64C7E275FA176574FC5AEB48A6E" xmlns="http://www.ni.com/PlatformFramework">
	<SourceModelFeatureSet>
		<ParsableNamespace AssemblyFileVersion="24.8.0.49911" FeatureSetName="InstrumentStudio Measurement UI" Name="http://www.ni.com/InstrumentFramework/ScreenDocument" OldestCompatibleVersion="22.1.0.1" Version="24.8.0.0" />
		<ParsableNamespace AssemblyFileVersion="9.14.0.49911" FeatureSetName="Editor" Name="http://www.ni.com/PlatformFramework" OldestCompatibleVersion="8.1.0.49152" Version="8.1.0.49152" />
		<ParsableNamespace AssemblyFileVersion="9.14.0.49911" FeatureSetName="SystemDesigner" Name="http://www.ni.com/SystemDesigner/EnvoyManagement" OldestCompatibleVersion="5.0.0.0" Version="5.0.0.49152" />
		<ParsableNamespace AssemblyFileVersion="9.14.0.49911" FeatureSetName="SystemDesigner" Name="http://www.ni.com/SystemDesigner/SystemDiagram" OldestCompatibleVersion="8.0.0.49152" Version="8.0.0.49152" />
		<ParsableNamespace AssemblyFileVersion="9.14.0.49911" FeatureSetName="SystemDesigner" Name="http://www.ni.com/SystemDesigner/SystemModelCore" OldestCompatibleVersion="5.1.0.5" Version="5.2.0.49152" />
		<ApplicationVersionInfo Build="24.8.0.49911" Name="Measurement Plug-In UI Editor" Version="24.8.0.49911" />
	</SourceModelFeatureSet>
	<Project xmlns="http://www.ni.com/PlatformFramework">
		<EnvoyManagerRootEnvoy Id="dd27c2d5c720415eb15215bd545c9daa" ModelDefinitionType="EnvoyManagerRootEnvoy" Name="RootEnvoy" />
		<EmbeddedDefinitionReference Id="89d719e01a084206ad23639db4b2f56f" ModelDefinitionType="NationalInstruments.ProjectExplorer.Modeling.ProjectDataManager" Name="ProjectExplorer">
			<ProjectExplorer />
		</EmbeddedDefinitionReference>
		<NameScopingEnvoy Id="595eaf9348434a23ae9cd79306a9f1cb" ModelDefinitionType="DefaultTarget" Name="DefaultTarget">
			<DefaultTarget />
			<SourceFileReference Id="82b9ddbcdf2948238df082fc48b602b7" ModelDefinitionType="{http://www.ni.com/InstrumentFramework/ScreenDocument}Screen" Name="${ui_file}" StoragePath="${ui_file}" />
		</NameScopingEnvoy>
		<EmbeddedDefinitionReference Id="e346ab41c93c4c81b47bf6d0522b5deb" ModelDefinitionType="NationalInstruments.SystemDesigner.SystemDiagram.SystemDiagramDefinition" Name="SystemDiagram">
			<SystemDiagram Id="1a63510b9b8443258bb044b34b362c63" SystemDiagramVersion="75" xmlns="http://www.ni.com/SystemDesigner/SystemDiagram">
				<EnvoySuperimpositionContainer Id="403e8b77a2104c37bbedb0ae13460459" xmlns="http://www.ni.com/SystemDesigner/EnvoyManagement">
					<MappingManager Id="9e777b028f4b469b8549ceadb6957a0a" xmlns="http://www.ni.com/SystemDesigner/SystemModelCore">
						<Superimposition Id="89235b0c03b1429dbc3dacc6a88e6f61" Name="Root Superimposition" />
					</MappingManager>
				</EnvoySuperimpositionContainer>
				<SystemDiagramRootDiagram Id="5a0c562a2db249768b0a8ecb33fd3041" />
			</SystemDiagram>
		</EmbeddedDefinitionReference>
		<NameScopingEnvoy Id="99031b5a162c4ef0ba572fcd38a9e9ef" ModelDefinitionType="NullTarget" Name="NullTarget">
			<NullTarget />
		</NameScopingEnvoy>
	</Project>
	<ProjectInformation xmlns="http://www.ni.com/PlatformFramework" />
</SourceFile>