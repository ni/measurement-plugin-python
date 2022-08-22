<%page args="ui_file"/>\
\
<?xml version="1.0" encoding="utf-8"?>
<SourceFile Checksum="D4F40B15EEEB05D24BA8051F9729BC2DA8B48AE96F7AACEDE9862C5EA8568A91110D7711921350CDD3C9C917BEFDC3FC9940EF949C36FCB693E1309265C33919" xmlns="http://www.ni.com/PlatformFramework">
	<SourceModelFeatureSet>
		<ParsableNamespace AssemblyFileVersion="22.8.0.1977" FeatureSetName="InstrumentStudio Measurement UI" Name="http://www.ni.com/InstrumentFramework/ScreenDocument" OldestCompatibleVersion="22.1.0.0" Version="22.1.0.0" />
		<ParsableNamespace AssemblyFileVersion="9.6.0.1977" FeatureSetName="Editor" Name="http://www.ni.com/PlatformFramework" OldestCompatibleVersion="8.1.0.49152" Version="8.1.0.49152" />
		<ApplicationVersionInfo Build="22.8.0.1977" Name="Measurement UI Editor" Version="22.8.0.1977" />
	</SourceModelFeatureSet>
	<Project xmlns="http://www.ni.com/PlatformFramework">
		<EnvoyManagerRootEnvoy Id="7b09cd53e16040cf8efb1be8e8c42fe7" ModelDefinitionType="EnvoyManagerRootEnvoy" Name="RootEnvoy" />
		<EmbeddedDefinitionReference Id="1f3aa3c38a764e90b075a8f62871f059" ModelDefinitionType="NationalInstruments.ProjectExplorer.Modeling.ProjectDataManager" Name="ProjectExplorer">
			<ProjectExplorer />
		</EmbeddedDefinitionReference>
		<NameScopingEnvoy Id="ebaa5b969dbe4c309b09213284188e4b" ModelDefinitionType="DefaultTarget" Name="DefaultTarget">
			<DefaultTarget />
			<SourceFileReference Id="729ac36108974b9bbb88eabbc64aa9ad" ModelDefinitionType="{http://www.ni.com/InstrumentFramework/ScreenDocument}Screen" Name="${ui_file}" StoragePath="${ui_file}" />
		</NameScopingEnvoy>
	</Project>
	<ProjectInformation xmlns="http://www.ni.com/PlatformFramework" />
</SourceFile>