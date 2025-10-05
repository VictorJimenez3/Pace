import '/flutter_flow/flutter_flow_icon_button.dart';
import '/flutter_flow/flutter_flow_theme.dart';
import '/flutter_flow/flutter_flow_util.dart';
import '/flutter_flow/flutter_flow_widgets.dart';
import '/flutter_flow/permissions_util.dart';
import '/index.dart';
import 'package:flutter/material.dart';
import 'package:font_awesome_flutter/font_awesome_flutter.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';
import 'package:record/record.dart';
import 'home_page_model.dart';
export 'home_page_model.dart';

class HomePageWidget extends StatefulWidget {
  const HomePageWidget({super.key});

  static String routeName = 'HomePage';
  static String routePath = '/homePage';

  @override
  State<HomePageWidget> createState() => _HomePageWidgetState();
}

class _HomePageWidgetState extends State<HomePageWidget> {
  late HomePageModel _model;

  final scaffoldKey = GlobalKey<ScaffoldState>();

  @override
  void initState() {
    super.initState();
    _model = createModel(context, () => HomePageModel());
  }

  @override
  void dispose() {
    _model.dispose();

    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    context.watch<FFAppState>();

    return GestureDetector(
      onTap: () {
        FocusScope.of(context).unfocus();
        FocusManager.instance.primaryFocus?.unfocus();
      },
      child: Scaffold(
        key: scaffoldKey,
        appBar: AppBar(
          backgroundColor: Color(0xFF57A8B3),
          automaticallyImplyLeading: false,
          leading: Align(
            alignment: AlignmentDirectional(0.0, -1.0),
            child: FlutterFlowIconButton(
              borderRadius: 8.0,
              buttonSize: 35.46,
              icon: FaIcon(
                FontAwesomeIcons.alignLeft,
                color: Colors.transparent,
                size: 24.0,
              ),
              onPressed: () async {
                context.pushNamed(ListWidget.routeName);
              },
            ),
          ),
          actions: [],
          flexibleSpace: FlexibleSpaceBar(
            background: ClipRRect(
              borderRadius: BorderRadius.circular(8.0),
              child: Image.asset(
                'assets/images/Gemini_Generated_Image_h3umych3umych3um_(1).jpg',
                fit: BoxFit.fitWidth,
                alignment: Alignment(0.0, 1.0),
              ),
            ),
          ),
          centerTitle: false,
          elevation: 2.0,
        ),
        body: Stack(
          children: [
            Align(
              alignment: AlignmentDirectional(0.0, 0.0),
              child: ClipRRect(
                borderRadius: BorderRadius.circular(0.0),
                child: Image.asset(
                  'assets/images/Gemini_Generated_Image_5f4d1w5f4d1w5f4d-min.jpg',
                  width: double.infinity,
                  height: double.infinity,
                  fit: BoxFit.fill,
                  alignment: Alignment(0.0, 0.0),
                ),
              ),
            ),
            Align(
              alignment: AlignmentDirectional(0.0, 0.0),
              child: Container(
                width: 150.0,
                height: 150.0,
                decoration: BoxDecoration(
                  color: FlutterFlowTheme.of(context).secondaryBackground,
                  shape: BoxShape.circle,
                ),
                alignment: AlignmentDirectional(0.0, 0.0),
                child: Stack(
                  children: [
                    Align(
                      alignment: AlignmentDirectional(0.0, 0.0),
                      child: Container(
                        width: 200.0,
                        height: 200.0,
                        clipBehavior: Clip.antiAlias,
                        decoration: BoxDecoration(
                          shape: BoxShape.circle,
                        ),
                        child: Image.asset(
                          'assets/images/Gemini_Generated_Image_2tyyln2tyyln2tyy_(1).jpg',
                          fit: BoxFit.cover,
                        ),
                      ),
                    ),
                    Opacity(
                      opacity: 0.0,
                      child: Align(
                        alignment: AlignmentDirectional(0.03, -0.04),
                        child: FFButtonWidget(
                          onPressed: () async {
                            await requestPermission(microphonePermission);
                            if (FFAppState().isRecording) {
                              await stopAudioRecording(
                                audioRecorder: _model.audioRecorder,
                                audioName: 'recordedFileBytes',
                                onRecordingComplete:
                                    (audioFilePath, audioBytes) {
                                  _model.recordedAudioPath = audioFilePath;
                                  _model.recordedFileBytes = audioBytes;
                                },
                              );

                              FFAppState().isRecording = false;
                              safeSetState(() {});
                            } else {
                              await startAudioRecording(
                                context,
                                audioRecorder: _model.audioRecorder ??=
                                    AudioRecorder(),
                              );

                              FFAppState().isRecording = true;
                              safeSetState(() {});
                            }

                            safeSetState(() {});
                          },
                          text: 'Button',
                          icon: Icon(
                            Icons.mic,
                            size: 15.0,
                          ),
                          options: FFButtonOptions(
                            height: double.infinity,
                            padding: EdgeInsetsDirectional.fromSTEB(
                                16.0, 0.0, 16.0, 0.0),
                            iconPadding: EdgeInsetsDirectional.fromSTEB(
                                0.0, 0.0, 0.0, 0.0),
                            color: Color(0xFF080808),
                            textStyle: FlutterFlowTheme.of(context)
                                .titleSmall
                                .override(
                                  font: GoogleFonts.interTight(
                                    fontWeight: FlutterFlowTheme.of(context)
                                        .titleSmall
                                        .fontWeight,
                                    fontStyle: FlutterFlowTheme.of(context)
                                        .titleSmall
                                        .fontStyle,
                                  ),
                                  color: Colors.white,
                                  letterSpacing: 0.0,
                                  fontWeight: FlutterFlowTheme.of(context)
                                      .titleSmall
                                      .fontWeight,
                                  fontStyle: FlutterFlowTheme.of(context)
                                      .titleSmall
                                      .fontStyle,
                                ),
                            elevation: 0.0,
                            borderRadius: BorderRadius.circular(24.0),
                          ),
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),
            Align(
              alignment: AlignmentDirectional(-0.01, 0.28),
              child: AnimatedDefaultTextStyle(
                style: FlutterFlowTheme.of(context).bodyMedium.override(
                  font: GoogleFonts.openSans(
                    fontWeight: FontWeight.bold,
                    fontStyle:
                        FlutterFlowTheme.of(context).bodyMedium.fontStyle,
                  ),
                  fontSize: 20.0,
                  letterSpacing: 0.0,
                  fontWeight: FontWeight.bold,
                  fontStyle: FlutterFlowTheme.of(context).bodyMedium.fontStyle,
                  shadows: [
                    Shadow(
                      color: FlutterFlowTheme.of(context).secondaryText,
                      offset: Offset(2.0, 2.0),
                      blurRadius: 2.0,
                    )
                  ],
                ),
                duration: Duration(milliseconds: 150),
                curve: Curves.easeInOut,
                child: Text(
                  'Tap to Start Recording!',
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
