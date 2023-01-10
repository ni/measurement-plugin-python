<%page args="display_name, service_class"/>\
\
<?xml version="1.0" encoding="utf-8"?>
<SourceFile Checksum="BDCAC3F8D8E3716B3E94E0FD086DD46820712B258DCAA34AB2518BD37944E507B9171022113DA7022D17735D0DD4EB8F7BF9FF126A9B26EAFB5385CE466A2328" Timestamp="1D924B702209D19" xmlns="http://www.ni.com/PlatformFramework">
	<SourceModelFeatureSet>
		<ParsableNamespace AssemblyFileVersion="9.7.0.49332" FeatureSetName="Configuration Based Software Core" Name="http://www.ni.com/ConfigurationBasedSoftware.Core" OldestCompatibleVersion="6.3.0.49152" Version="6.3.0.49152" />
		<ParsableNamespace AssemblyFileVersion="9.7.0.49332" FeatureSetName="LabVIEW Controls" Name="http://www.ni.com/Controls.LabVIEW.Design" OldestCompatibleVersion="8.1.0.49152" Version="8.1.0.49152" />
		<ParsableNamespace AssemblyFileVersion="23.0.0.49332" FeatureSetName="InstrumentStudio Measurement UI" Name="http://www.ni.com/InstrumentFramework/ScreenDocument" OldestCompatibleVersion="22.1.0.1" Version="22.1.0.1" />
		<ParsableNamespace AssemblyFileVersion="9.7.0.49332" FeatureSetName="Editor" Name="http://www.ni.com/PanelCommon" OldestCompatibleVersion="6.1.0.0" Version="6.1.0.49152" />
		<ParsableNamespace AssemblyFileVersion="9.7.0.49332" FeatureSetName="Editor" Name="http://www.ni.com/PlatformFramework" OldestCompatibleVersion="8.1.0.49152" Version="8.1.0.49152" />
		<ApplicationVersionInfo Build="23.0.0.49332" Name="MeasurementLink UI Editor" Version="23.0.0.49332" />
	</SourceModelFeatureSet>
	<Screen ClientId="{c652bbf0-7148-496d-85fe-06653cd41eaf}" DisplayName="${display_name}" Id="951ada7311244fc186690f66be50fe48" ServiceClass="${service_class}" xmlns="http://www.ni.com/InstrumentFramework/ScreenDocument">
		<ScreenSurface Height="[float]400" Id="98b2ef21e0a14a49bdce21ce0e6ffd5d" Left="[float]0" PanelSizeMode="Fixed" Top="[float]0" Width="[float]800" xmlns="http://www.ni.com/ConfigurationBasedSoftware.Core">
			<ScreenSurfaceCanvas Background="[SMSolidColorBrush]#80808080" BaseName="[string]Canvas" Height="[float]155" Id="18409ed2a6834e3c9d16482ce12d4456" Label="[UIModel]4cf4adf12c947918b5397e14dbe63ea" Left="[float]25" Top="[float]31" Width="[float]134">
				<ChannelArrayViewer AdaptsToType="[bool]True" ArrayElement="[UIModel]e87ce07b6f2748068bb6ee94f8a9f950" BaseName="[string]Numeric Array Input" Channel="[string]Configuration/Array in" Columns="[int]1" Dimensions="[int]1" Height="[float]120" Id="47ce4cf9a7ba483b9302b38396cecd3f" IndexVisibility="[Visibility]Collapsed" Label="[UIModel]e047fd7a7506489286d7cd1895155531" Left="[float]11" Orientation="[SMOrientation]Vertical" Rows="[int]4" Top="[float]26" VerticalScrollBarVisibility="[ScrollBarVisibility]Visible" Width="[float]104">
					<p.DefaultElementValue>0x0</p.DefaultElementValue>
					<ChannelArrayNumericText BaseName="[string]Numeric" Height="[float]24" Id="e87ce07b6f2748068bb6ee94f8a9f950" UnitAnnotation="[string]" ValueFormatter="[string]LV:G5" ValueType="[Type]Double" Width="[float]72" />
				</ChannelArrayViewer>
				<Label Height="[float]16" Id="e047fd7a7506489286d7cd1895155531" LabelOwner="[UIModel]47ce4cf9a7ba483b9302b38396cecd3f" Left="[float]11" Text="[string]Array in" Top="[float]2" Width="[float]41" xmlns="http://www.ni.com/PanelCommon" />
			</ScreenSurfaceCanvas>
			<Label Height="[float]16" Id="4cf4adf12c947918b5397e14dbe63ea" LabelOwner="[UIModel]18409ed2a6834e3c9d16482ce12d4456" Left="[float]25" Text="[string]Input" Top="[float]11" Width="[float]28" xmlns="http://www.ni.com/PanelCommon" />
			<ScreenSurfaceCanvas Background="[SMSolidColorBrush]#80808080" BaseName="[string]Canvas" Height="[float]155" Id="c380edefe8e43fe9bec7aa3789c4ac9" Label="[UIModel]418004886c464b879c0b1a356b4a0a96" Left="[float]207" Top="[float]31" Width="[float]134">
				<ChannelArrayViewer AdaptsToType="[bool]True" ArrayElement="[UIModel]424a12e4d68a4b948d2613ca4c3908a6" BaseName="[string]Numeric Array Output" Channel="[string]Output/Array out" Columns="[int]1" Dimensions="[int]1" Height="[float]120" Id="af62731a9eab4296ab89339950e542d6" IndexVisibility="[Visibility]Collapsed" Label="[UIModel]8b3d1fbb5c68438695c70ab5a8377ac2" Left="[float]10" Orientation="[SMOrientation]Vertical" Rows="[int]4" Top="[float]27" VerticalScrollBarVisibility="[ScrollBarVisibility]Visible" Width="[float]104">
					<p.DefaultElementValue>0x0</p.DefaultElementValue>
					<ChannelArrayNumericText BaseName="[string]Numeric" Height="[float]24" Id="424a12e4d68a4b948d2613ca4c3908a6" IsReadOnly="[bool]True" UnitAnnotation="[string]" ValueFormatter="[string]LV:G5" ValueType="[Type]Double" Width="[float]72" />
				</ChannelArrayViewer>
				<Label Height="[float]16" Id="8b3d1fbb5c68438695c70ab5a8377ac2" LabelOwner="[UIModel]af62731a9eab4296ab89339950e542d6" Left="[float]10" Text="[string]Array out" Top="[float]7" Width="[float]49" xmlns="http://www.ni.com/PanelCommon" />
			</ScreenSurfaceCanvas>
			<Label Height="[float]16" Id="418004886c464b879c0b1a356b4a0a96" LabelOwner="[UIModel]c380edefe8e43fe9bec7aa3789c4ac9" Left="[float]207" Text="[string]Output" Top="[float]11" Width="[float]38" xmlns="http://www.ni.com/PanelCommon" />
		</ScreenSurface>
	</Screen>
</SourceFile>