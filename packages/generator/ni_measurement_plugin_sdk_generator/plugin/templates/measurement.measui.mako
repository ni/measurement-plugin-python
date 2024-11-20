<%page args="display_name, service_class"/>\
\
<?xml version="1.0" encoding="utf-8"?>
<SourceFile Checksum="C68495BACA801D17201A400444BA8E57096D877C220B005C9CC754DDBC96D7FF74F6512D245FAE462DBE92AF734E428F52FD46C680D4C1315BDAFF8C1B569796" Timestamp="1DB3B1ED4C5A7FD" xmlns="http://www.ni.com/PlatformFramework">
	<SourceModelFeatureSet>
		<ParsableNamespace AssemblyFileVersion="9.14.0.49911" FeatureSetName="Configuration Based Software Core" Name="http://www.ni.com/ConfigurationBasedSoftware.Core" OldestCompatibleVersion="6.3.0.49152" Version="9.8.1.49152" />
		<ParsableNamespace AssemblyFileVersion="9.14.0.49911" FeatureSetName="LabVIEW Controls" Name="http://www.ni.com/Controls.LabVIEW.Design" OldestCompatibleVersion="8.1.0.49152" Version="8.1.0.49152" />
		<ParsableNamespace AssemblyFileVersion="24.8.0.49911" FeatureSetName="InstrumentStudio Measurement UI" Name="http://www.ni.com/InstrumentFramework/ScreenDocument" OldestCompatibleVersion="22.1.0.1" Version="24.8.0.0" />
		<ParsableNamespace AssemblyFileVersion="9.14.0.49911" FeatureSetName="Editor" Name="http://www.ni.com/PanelCommon" OldestCompatibleVersion="6.1.0.0" Version="6.1.0.49152" />
		<ParsableNamespace AssemblyFileVersion="9.14.0.49911" FeatureSetName="Editor" Name="http://www.ni.com/PlatformFramework" OldestCompatibleVersion="8.1.0.49152" Version="8.1.0.49152" />
		<ApplicationVersionInfo Build="24.8.0.49911" Name="Measurement Plug-In UI Editor" Version="24.8.0.49911" />
	</SourceModelFeatureSet>
	<Screen DisplayName="${display_name}" Id="3656de7c9d6a42cfb27ea41494f0ed46" ServiceClass="${service_class}" xmlns="http://www.ni.com/InstrumentFramework/ScreenDocument">
		<ScreenSurface BackgroundColor="[SMSolidColorBrush]#ffffffff" Height="[float]400" Id="5c1b8cc5eaf94b12b2be341f38937113" Left="[float]0" PanelSizeMode="Fixed" Top="[float]0" Width="[float]800" xmlns="http://www.ni.com/ConfigurationBasedSoftware.Core">
			<ChannelArrayViewer AdaptsToType="[bool]True" ArrayElement="[UIModel]6f8ab70f7a984a76ab50c8963cdebdfc" BaseName="[string]Numeric Array Input" Channel="[string]{5541d3fb-67cf-41cb-af53-b51b5b84fe2c}/Configuration/Array in" Columns="[int]1" Dimensions="[int]1" Height="[float]120" Id="4c034db32a2a40ce8ce645cda760a0bc" IndexVisibility="[Visibility]Collapsed" IsFixedSize="[bool]False" Label="[UIModel]1eff9af8bfcd427b919b514abb7494d9" Left="[float]34" Orientation="[SMOrientation]Vertical" Rows="[int]4" TabIndex="[int]0" Top="[float]50" VerticalScrollBarVisibility="[ScrollBarVisibility]Visible" Width="[float]104">
				<p.DefaultElementValue>0x0</p.DefaultElementValue>
				<ChannelArrayNumericText BaseName="[string]Numeric" Height="[float]24" Id="6f8ab70f7a984a76ab50c8963cdebdfc" UnitAnnotation="[string]" ValueFormatter="[string]LV:G5" ValueType="[Type]Double" Width="[float]72" />
			</ChannelArrayViewer>
			<Label Height="[float]16" Id="1eff9af8bfcd427b919b514abb7494d9" LabelOwner="[UIModel]4c034db32a2a40ce8ce645cda760a0bc" Left="[float]34" Text="[string]Array in" Top="[float]30" Width="[float]41" xmlns="http://www.ni.com/PanelCommon" />
			<ChannelArrayViewer AdaptsToType="[bool]True" ArrayElement="[UIModel]2601f80845974011b1488c655006560d" BaseName="[string]Numeric Array Output" Channel="[string]{5541d3fb-67cf-41cb-af53-b51b5b84fe2c}/Output/Array out" Columns="[int]1" Dimensions="[int]1" Height="[float]120" Id="48aa4906df6b47cf9e0404db2300ea9f" IndexVisibility="[Visibility]Collapsed" IsFixedSize="[bool]False" Label="[UIModel]107983d1f11646ee84e5159106f36b81" Left="[float]202" Orientation="[SMOrientation]Vertical" Rows="[int]4" TabIndex="[int]1" Top="[float]50" VerticalScrollBarVisibility="[ScrollBarVisibility]Visible" Width="[float]104">
				<p.DefaultElementValue>0x0</p.DefaultElementValue>
				<ChannelArrayNumericText BaseName="[string]Numeric" Height="[float]24" Id="2601f80845974011b1488c655006560d" IsReadOnly="[bool]True" UnitAnnotation="[string]" ValueFormatter="[string]LV:G5" ValueType="[Type]Double" Width="[float]72" />
			</ChannelArrayViewer>
			<Label Height="[float]16" Id="107983d1f11646ee84e5159106f36b81" LabelOwner="[UIModel]48aa4906df6b47cf9e0404db2300ea9f" Left="[float]202" Text="[string]Array out" Top="[float]30" Width="[float]49" xmlns="http://www.ni.com/PanelCommon" />
		</ScreenSurface>
	</Screen>
</SourceFile>