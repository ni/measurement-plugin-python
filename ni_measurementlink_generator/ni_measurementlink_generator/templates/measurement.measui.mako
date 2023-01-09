<%page args="display_name, service_class"/>\
\
<?xml version="1.0" encoding="utf-8"?>
<SourceFile Checksum="037219FA3793B0345BA296B3AA1C5142A02A9F7B690D59A1689A7635A44D206FAA09937ACF8AD2A224CA4E48743E599D15A0B12F305068706D1AD32AA25315DC" Timestamp="1D92416E545F4CF" xmlns="http://www.ni.com/PlatformFramework">
	<SourceModelFeatureSet>
		<ParsableNamespace AssemblyFileVersion="9.7.0.1787" FeatureSetName="Configuration Based Software Core" Name="http://www.ni.com/ConfigurationBasedSoftware.Core" OldestCompatibleVersion="6.3.0.49152" Version="6.3.0.49152" />
		<ParsableNamespace AssemblyFileVersion="9.7.0.1787" FeatureSetName="LabVIEW Controls" Name="http://www.ni.com/Controls.LabVIEW.Design" OldestCompatibleVersion="8.1.0.49152" Version="8.1.0.49152" />
		<ParsableNamespace AssemblyFileVersion="23.3.0.202" FeatureSetName="InstrumentStudio Measurement UI" Name="http://www.ni.com/InstrumentFramework/ScreenDocument" OldestCompatibleVersion="22.1.0.1" Version="22.1.0.1" />
		<ParsableNamespace AssemblyFileVersion="9.7.0.1787" FeatureSetName="Editor" Name="http://www.ni.com/PanelCommon" OldestCompatibleVersion="6.1.0.0" Version="6.1.0.49152" />
		<ParsableNamespace AssemblyFileVersion="9.8.0.92" FeatureSetName="Editor" Name="http://www.ni.com/PlatformFramework" OldestCompatibleVersion="8.1.0.49152" Version="8.1.0.49152" />
		<ApplicationVersionInfo Build="23.3.0.92" Name="MeasurementLink UI Editor" Version="23.3.0.92" />
	</SourceModelFeatureSet>
	<Screen ClientId="{8b26097f-29a0-469a-9f79-f0deb83aa231}" DisplayName="${display_name}" Id="f344597c0c6c4879b2a44dd8e7731ca4" ServiceClass="${service_class}" xmlns="http://www.ni.com/InstrumentFramework/ScreenDocument">
		<ScreenSurface Height="[float]400" Id="236c55a7f4cc4e46844ea0cb684f0fdf" Left="[float]0" PanelSizeMode="Fixed" Top="[float]0" Width="[float]800" xmlns="http://www.ni.com/ConfigurationBasedSoftware.Core">
			<ScreenSurfaceCanvas Background="[SMSolidColorBrush]#80808080" BaseName="[string]Canvas" Height="[float]155" Id="393cf39ea0ae450f8aafa0d4a44b80da" Label="[UIModel]ddd3794b6d76479690b14eeea4cfad06" Left="[float]25" Top="[float]31" Width="[float]134">
				<ChannelArrayViewer AdaptsToType="[bool]True" ArrayElement="[UIModel]3d703cb8849940288d65265c467cbf3f" BaseName="[string]Numeric Array Input" Channel="[string]Configuration/Array in" Columns="[int]1" Dimensions="[int]1" Height="[float]120" Id="2f06a36bcd734d5eb5f3a431c713156f" IndexVisibility="[Visibility]Collapsed" Label="[UIModel]1dfaedaffb434dd0a6a2c3d082014053" Left="[float]11" Orientation="[SMOrientation]Vertical" Rows="[int]4" TabIndex="[int]0" Top="[float]26" VerticalScrollBarVisibility="[ScrollBarVisibility]Visible" Width="[float]104">
					<p.DefaultElementValue>0x0</p.DefaultElementValue>
					<ChannelArrayNumericText BaseName="[string]Numeric" Height="[float]24" Id="3d703cb8849940288d65265c467cbf3f" UnitAnnotation="[string]" ValueFormatter="[string]LV:G5" ValueType="[Type]Double" Width="[float]72" />
				</ChannelArrayViewer>
				<Label Height="[float]16" Id="1dfaedaffb434dd0a6a2c3d082014053" LabelOwner="[UIModel]2f06a36bcd734d5eb5f3a431c713156f" Left="[float]11" Text="[string]Array in" Top="[float]6" Width="[float]41" xmlns="http://www.ni.com/PanelCommon" />
			</ScreenSurfaceCanvas>
			<Label Height="[float]16" Id="ddd3794b6d76479690b14eeea4cfad06" LabelOwner="[UIModel]393cf39ea0ae450f8aafa0d4a44b80da" Left="[float]25" Text="[string]Input" Top="[float]11" Width="[float]28" xmlns="http://www.ni.com/PanelCommon" />
			<ScreenSurfaceCanvas Background="[SMSolidColorBrush]#80808080" BaseName="[string]Canvas" Height="[float]155" Id="24d6e8e71de34cd8a7e6524e35a1d3a6" Label="[UIModel]25e5f3e04a8345e58aa1baf42f32654c" Left="[float]207" Top="[float]31" Width="[float]134">
				<ChannelArrayViewer AdaptsToType="[bool]True" ArrayElement="[UIModel]a4ae6b7928654a1f8d0324384fe8da8a" BaseName="[string]Numeric Array Output" Channel="[string]Output/Array out" Columns="[int]1" Dimensions="[int]1" Height="[float]120" Id="3a8285c9eae048df8b515bd726230a3c" IndexVisibility="[Visibility]Collapsed" Label="[UIModel]dfb7576888ea4721a0fc54f6046b193f" Left="[float]10" Orientation="[SMOrientation]Vertical" Rows="[int]4" TabIndex="[int]0" Top="[float]27" VerticalScrollBarVisibility="[ScrollBarVisibility]Visible" Width="[float]104">
					<p.DefaultElementValue>0x0</p.DefaultElementValue>
					<ChannelArrayNumericText BaseName="[string]Numeric" Height="[float]24" Id="a4ae6b7928654a1f8d0324384fe8da8a" IsReadOnly="[bool]True" UnitAnnotation="[string]" ValueFormatter="[string]LV:G5" ValueType="[Type]Double" Width="[float]72" />
				</ChannelArrayViewer>
				<Label Height="[float]16" Id="dfb7576888ea4721a0fc54f6046b193f" LabelOwner="[UIModel]3a8285c9eae048df8b515bd726230a3c" Left="[float]11" Text="[string]Array out" Top="[float]7" Width="[float]49" xmlns="http://www.ni.com/PanelCommon" />
			</ScreenSurfaceCanvas>
			<Label Height="[float]16" Id="25e5f3e04a8345e58aa1baf42f32654c" LabelOwner="[UIModel]24d6e8e71de34cd8a7e6524e35a1d3a6" Left="[float]207" Text="[string]Output" Top="[float]11" Width="[float]38" xmlns="http://www.ni.com/PanelCommon" />
		</ScreenSurface>
	</Screen>
</SourceFile>