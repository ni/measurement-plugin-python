<%page args="display_name, service_class"/>\
\
<?xml version="1.0" encoding="utf-8"?>
<SourceFile Checksum="F6BC453A030B5A154B8AA72258BE892CEC0C544EA4EA406EE2BE4D88932478C05B29F9D74FB1DFDB6603EC46C77B7C757160E6413A7CFC6C971302FF7C4D5903" Timestamp="1D89D49951B3C35" xmlns="http://www.ni.com/PlatformFramework">
	<SourceModelFeatureSet>
		<ParsableNamespace AssemblyFileVersion="9.6.0.975" FeatureSetName="Configuration Based Software Core" Name="http://www.ni.com/ConfigurationBasedSoftware.Core" OldestCompatibleVersion="6.3.0.49152" Version="6.3.0.49152" />
		<ParsableNamespace AssemblyFileVersion="9.6.0.975" FeatureSetName="LabVIEW Controls" Name="http://www.ni.com/Controls.LabVIEW.Design" OldestCompatibleVersion="8.1.0.49152" Version="8.1.0.49152" />
		<ParsableNamespace AssemblyFileVersion="22.8.0.975" FeatureSetName="InstrumentStudio Measurement UI" Name="http://www.ni.com/InstrumentFramework/ScreenDocument" OldestCompatibleVersion="22.1.0.0" Version="22.1.0.0" />
		<ParsableNamespace AssemblyFileVersion="9.6.0.975" FeatureSetName="Editor" Name="http://www.ni.com/PanelCommon" OldestCompatibleVersion="6.1.0.0" Version="6.1.0.49152" />
		<ParsableNamespace AssemblyFileVersion="9.6.0.975" FeatureSetName="Editor" Name="http://www.ni.com/PlatformFramework" OldestCompatibleVersion="8.1.0.49152" Version="8.1.0.49152" />
		<ApplicationVersionInfo Build="22.8.0.975" Name="Measurement UI Editor" Version="22.8.0.975" />
	</SourceModelFeatureSet>
	<Screen ClientId="{f2193b1d-1b6e-450a-b051-b268966356ce}" DisplayName="${display_name}" Id="172a7c38b0dc4ac6b18ca4397c8d6832" ServiceClass="${service_class}" xmlns="http://www.ni.com/InstrumentFramework/ScreenDocument">
		<ScreenSurface Height="[float]400" Id="5996746ebab246d8ace75a4305e4a290" Left="[float]0" PanelSizeMode="Fixed" Top="[float]0" Width="[float]800" xmlns="http://www.ni.com/ConfigurationBasedSoftware.Core">
			<ScreenSurfaceCanvas Background="[SMSolidColorBrush]#80808080" BaseName="[string]Canvas" Height="[float]155" Id="2af6108da1054dc9a76e83663d3e6a69" Label="[UIModel]d75763afd14e48838daea830ed6372e1" Left="[float]25" Top="[float]31" Width="[float]134">
				<ChannelArrayViewer AdaptsToType="[bool]True" ArrayElement="[UIModel]42af83617b204148b9f703d86ddad9f2" BaseName="[string]Numeric Array Input" Channel="[string]Configuration/Array in" Columns="[int]1" Dimensions="[int]1" Height="[float]120" Id="62525389c3647d595a3583252b623c0" IndexVisibility="[Visibility]Collapsed" Label="[UIModel]ba7278f5626c4b8ea67bb08286c51d21" Left="[float]11" Orientation="[SMOrientation]Vertical" Rows="[int]4" Top="[float]26" VerticalScrollBarVisibility="[ScrollBarVisibility]Visible" Width="[float]104">
					<p.DefaultElementValue>0x0</p.DefaultElementValue>
					<ChannelArrayNumericText BaseName="[string]Numeric" Height="[float]24" Id="42af83617b204148b9f703d86ddad9f2" UnitAnnotation="[string]" ValueFormatter="[string]LV:G5" ValueType="[Type]Double" Width="[float]72" />
				</ChannelArrayViewer>
				<Label Height="[float]16" Id="ba7278f5626c4b8ea67bb08286c51d21" LabelOwner="[UIModel]62525389c3647d595a3583252b623c0" Left="[float]11" Text="[string]Array in" Top="[float]6" Width="[float]41" xmlns="http://www.ni.com/PanelCommon" />
			</ScreenSurfaceCanvas>
			<Label Height="[float]16" Id="d75763afd14e48838daea830ed6372e1" LabelOwner="[UIModel]2af6108da1054dc9a76e83663d3e6a69" Left="[float]25" Text="[string]Input" Top="[float]11" Width="[float]28" xmlns="http://www.ni.com/PanelCommon" />
			<ScreenSurfaceCanvas Background="[SMSolidColorBrush]#80808080" BaseName="[string]Canvas" Height="[float]155" Id="bdbab52d1a884aa6a37de7a4911309a3" Label="[UIModel]66e07f634ac64c3fa47cd4cf37a5d244" Left="[float]207" Top="[float]31" Width="[float]134">
				<ChannelArrayViewer AdaptsToType="[bool]True" ArrayElement="[UIModel]5b0ecf3b36c94ca19be98db9e002aec2" BaseName="[string]Numeric Array Output" Channel="[string]Output/Array out" Columns="[int]1" Dimensions="[int]1" Height="[float]120" Id="440509c9226d4bcaa6e23a49125c2798" IndexVisibility="[Visibility]Collapsed" Label="[UIModel]3872fcc74c6e4427a6c1522d52bd16f1" Left="[float]11" Orientation="[SMOrientation]Vertical" Rows="[int]4" Top="[float]27" VerticalScrollBarVisibility="[ScrollBarVisibility]Visible" Width="[float]104">
					<p.DefaultElementValue>0x0</p.DefaultElementValue>
					<ChannelArrayNumericText BaseName="[string]Numeric" Height="[float]24" Id="5b0ecf3b36c94ca19be98db9e002aec2" IsReadOnly="[bool]True" UnitAnnotation="[string]" ValueFormatter="[string]LV:G5" ValueType="[Type]Double" Width="[float]72" />
				</ChannelArrayViewer>
				<Label Height="[float]16" Id="3872fcc74c6e4427a6c1522d52bd16f1" LabelOwner="[UIModel]440509c9226d4bcaa6e23a49125c2798" Left="[float]11" Text="[string]Array out" Top="[float]7" Width="[float]49" xmlns="http://www.ni.com/PanelCommon" />
			</ScreenSurfaceCanvas>
			<Label Height="[float]16" Id="66e07f634ac64c3fa47cd4cf37a5d244" LabelOwner="[UIModel]bdbab52d1a884aa6a37de7a4911309a3" Left="[float]207" Text="[string]Output" Top="[float]11" Width="[float]38" xmlns="http://www.ni.com/PanelCommon" />
		</ScreenSurface>
	</Screen>
</SourceFile>