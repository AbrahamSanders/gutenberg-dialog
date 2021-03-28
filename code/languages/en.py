import re
import unicodedata
from languages.lang import Lang


class En(Lang):
    def delimiters(self):
        def d1(delimiter, line):
            return line.count(delimiter)

        def d2(delimiter, line):
            return line.count(delimiter) * 2

        def d3(delimiter, line):
            if line[0] == delimiter:
                return 1
            return 0

        # Dictionary of delimiters and their respective counting functions.
        return {'"': d1, '“': d2, '‘': d2, '_': d3}

    def process_file_(self, paragraph_list):
        # After some amount of characters interpret utterance as new dialog.
        chars_since_dialog = self.cfg.dialog_gap + 1
        for p in paragraph_list:
            # If the paragraph potentially contains dialog.
            if len(p) > 1:
                if '_' == p[0]:
                    # If max chars exceeded start new dialog.
                    if chars_since_dialog > self.cfg.dialog_gap:
                        self.dialogs.append([])

                    utt = ''
                    # Augment the segment so the splitting will be correct.
                    segments = ('YXC' + p).split('_')

                    # Join into a single utterance since we are in a paragraph.
                    if len(segments) > 2:
                        utt = ' '.join(segments[2:])
                        self.dialogs[-1].append(' '.join(utt.split()))

                    chars_since_dialog = 0
                else:
                    # Add the whole paragraph since there were no dialog.
                    chars_since_dialog += len(p)

    # Extract the dialogs from one file.
    def process_file(self, paragraph_list, delimiter):
        if delimiter == '_':
            self.process_file_(paragraph_list)
            return

        # We have to deal with single quatation marks.
        if delimiter == '‘':
            paragraph_list = [p.replace('’ ', '‘ ')for p in paragraph_list]
        # Unify the later processing.
        if delimiter == '“':
            paragraph_list = [p.replace('”', '“')for p in paragraph_list]

        # After some amount of characters interpret utterance as new dialog.
        chars_since_dialog = self.cfg.dialog_gap + 1
        # Keep track of the last paragraph in addition to the current one for
        # use when including surrounding narratives.
        last_p = ''
        last_p_has_dialog = False
        for p in paragraph_list:
            p_has_dialog = False
            # If the paragraph potentially contains dialog.
            if delimiter in p:
                # If max chars exceeded start new dialog.
                if chars_since_dialog > self.cfg.dialog_gap:
                    self.dialogs.append([])

                utt = []
                # Augment the segment so the splitting will always be correct.
                segments = ('YXC' + p + 'YXC').split(delimiter)

                good_segment = True
                # Parse dialog utterances and intermediate narrative segments since we are inside a paragraph.
                if len(segments) > 2 and len(segments) % 2 == 1:
                    combine_dialogs = True
                    for i, segment in enumerate(segments):
                        if i == 1 and len(segment):
                            # 1st utt should be upper-case to avoid artifacts.
                            # Sometimes the 1st character can be a non-word character like an underscore for effect,
                            # in which case we want to see if the second character is upper-case.
                            upper_pos = 1 if (len(segment) > 1 and re.match('[^a-zA-Z0-9 ]', segment[0])) else 0
                            if segment[upper_pos] == segment[upper_pos].lower():
                                good_segment = False
                                break
                        if i % 2 == 1:
                            # Handle dialog utterances
                            if combine_dialogs and len(utt) > 0:
                                utt[-1] += ' %s' % ' '.join(segment.split())
                            else:
                                prefix = '[D]: ' if self.cfg.include_surrounding_narratives else ''
                                utt.append('%s%s' % (prefix, ' '.join(segment.split())))                                
                        elif self.cfg.include_surrounding_narratives:
                            # Handle intermediate narrative segments 
                            # (nested before, between, or after dialog utterances within the same paragraph)
                            if segment.startswith('YXC'):
                                segment = segment[3:]
                            elif segment.endswith('YXC'):
                                segment = segment[:-3]
                            sub_segments = segment.split()
                            # If we omit an intermediate narrative which is too short, any immediately following dialog
                            # within the same paragraph should be combined with the previous one.
                            combine_dialogs = True
                            if len(sub_segments) >= self.cfg.min_intermediate_narrative_length:
                                segment = ' '.join(sub_segments)
                                # remove any leading non-word or non-opening characters from the narrative segment
                                segment = re.sub(r'\A[^\w([{`\'‘"“-]+', '', segment)
                                if segment != '':
                                    utt.append('[N]: %s' % segment)
                                    # We did not omit this narrative segment so we won't combine
                                    # any immediately following dialog.
                                    combine_dialogs = False

                    if good_segment:
                        p_has_dialog = True
                        if self.cfg.include_surrounding_narratives:
                            if not last_p_has_dialog and last_p != '':
                                # If including surrounding narratives, add the preceding narrative unless it is
                                # the same as the last proceeding narrative within the same dialog sequence.
                                preceding_narrative = '[N]: %s' % last_p
                                if len(self.dialogs[-1]) == 0 or self.dialogs[-1][-1] != preceding_narrative:
                                    self.dialogs[-1].append(preceding_narrative)
                        self.dialogs[-1].extend(utt)

                # Add chars after last comma.
                if good_segment:
                    chars_since_dialog = len(segments[-1]) - 3
                else:
                    chars_since_dialog += len(p)
            else:
                # Otherwise add the whole paragraph since there was no dialog.
                chars_since_dialog += len(p)
            
            # If including surrounding narratives, add the proceeding narrative. 
            if self.cfg.include_surrounding_narratives and last_p_has_dialog and not p_has_dialog and p != '':
                self.dialogs[-1].append('[N]: %s' % p)

            # Remember the last paragraph
            last_p = p
            last_p_has_dialog = p_has_dialog

    def clean_line(self, line):
        line = re.sub(' \' ', '\'', line)
        line = unicodedata.normalize('NFKD', line)

        # Keep some special tokens.
        line = re.sub('[^a-z .,-:?!"\'0-9]', '', line)
        line = re.sub('[.]', ' . ', line)
        line = re.sub('[?]', ' ? ', line)
        line = re.sub('[!]', ' ! ', line)
        line = re.sub('[-]', ' - ', line)
        line = re.sub('["]', ' " ', line)
        line = re.sub('[:]', ' : ', line)
        line = re.sub('[,]', ' , ', line)
        return line
