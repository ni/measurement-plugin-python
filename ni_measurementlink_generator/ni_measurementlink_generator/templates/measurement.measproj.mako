<%page args="ui_file"/>\
\
<?xml version="1.0" encoding="utf-8"?>
<SourceFile Checksum="D75F992328C5D7515D9D415BD6A735FA591B6E5166671A3EDAAE0DA526541089828917B78BD7BD71409844922699BFC30CB6497F7CD8B6753585526A9B7B43DD" xmlns="http://www.ni.com/PlatformFramework">
	<SourceModelFeatureSet>
		<ParsableNamespace AssemblyFileVersion="23.0.0.49332" FeatureSetName="InstrumentStudio Measurement UI" Name="http://www.ni.com/InstrumentFramework/ScreenDocument" OldestCompatibleVersion="22.1.0.1" Version="22.1.0.1" />
		<ParsableNamespace AssemblyFileVersion="9.7.0.49332" FeatureSetName="Editor" Name="http://www.ni.com/PlatformFramework" OldestCompatibleVersion="8.1.0.49152" Version="8.1.0.49152" />
		<ApplicationVersionInfo Build="23.0.0.49332" Name="MeasurementLink UI Editor" Version="23.0.0.49332" />
	</SourceModelFeatureSet>
	<Project xmlns="http://www.ni.com/PlatformFramework">
		<EnvoyManagerRootEnvoy Id="6a601cfa53834724b3e46aa0445e25a0" ModelDefinitionType="EnvoyManagerRootEnvoy" Name="RootEnvoy" />
		<EmbeddedDefinitionReference Id="3f1bd45184744d6595d6d7b008662efc" ModelDefinitionType="NationalInstruments.ProjectExplorer.Modeling.ProjectDataManager" Name="ProjectExplorer">
			<ProjectExplorer />
		</EmbeddedDefinitionReference>
		<NameScopingEnvoy Id="a7e9c36db3194f71869079e48ac6397e" ModelDefinitionType="DefaultTarget" Name="DefaultTarget">
			<DefaultTarget />
			<SourceFileReference Id="7d137e4ffec6485693839b2b92093077" ModelDefinitionType="{http://www.ni.com/InstrumentFramework/ScreenDocument}Screen" Name="${ui_file}" StoragePath="${ui_file}" />
		</NameScopingEnvoy>
	</Project>
	<ProjectInformation xmlns="http://www.ni.com/PlatformFramework" />
</SourceFile>